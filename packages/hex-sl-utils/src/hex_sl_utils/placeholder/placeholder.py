from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any, cast

from hex_sl_utils._vendor.sqlglot import Generator, Parser, exp
from hex_sl_utils._vendor.sqlglot.tokens import TokenType
from hex_sl_utils.datatype import DataType, datatype_to_sqlglot
from hex_sl_utils.exception import UserFacingError
from hex_sl_utils.placeholder.placeholder_style import PlaceholderStyle
from hex_sl_utils.utils import assert_unreachable

# Constant for semantic placeholder kind (${...} style)
PLACEHOLDER_KIND_SEMANTIC = "semantic"
PLACEHOLDER_OFFSET_META = "hexsl_placeholder_offset"
PLACEHOLDER_RECORD_ORDER_META = "_hexsl_record_placeholder_order"


@dataclass
class PlaceholderConfig:
    mode: PlaceholderStyle
    all_parameters: dict[str, DataType]
    used_parameters: dict[str, DataType]
    order: list[str]
    occurrences: list[str] = field(default_factory=list, repr=False, compare=False)
    parameter_order: list[str] = field(default_factory=list, repr=False, compare=False)
    infer_parameters: bool = field(default=False, repr=False, compare=False)
    parse_position: int = field(default=0, repr=False, compare=False)
    # Maps a placeholder token's source offset -> the positional index it was
    # assigned. sqlglot can re-invoke the placeholder parser for the same token
    # while backtracking (e.g. LIMIT parsing retreats and re-parses), so keying
    # by offset keeps assignment idempotent instead of advancing the counter on
    # every retry.
    position_by_offset: dict[int, int] = field(
        default_factory=dict, repr=False, compare=False
    )
    parse_occurrences_by_offset: dict[int, str] = field(
        default_factory=dict, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        # Sort the dictionaries by key for consistent snapshot testing
        self.all_parameters = dict(sorted(self.all_parameters.items()))
        self.used_parameters = dict(sorted(self.used_parameters.items()))

    def as_public_dict(self) -> dict[str, object]:
        return {
            "mode": self.mode,
            "all_parameters": self.all_parameters,
            "used_parameters": self.used_parameters,
            "order": self.order,
        }


# Thread-safe storage for placeholder config using contextvars
_placeholder_config: ContextVar[PlaceholderConfig | None] = ContextVar(
    "placeholder_config", default=None
)


def get_placeholder_config() -> PlaceholderConfig | None:
    """Get the current placeholder config for this context."""
    return _placeholder_config.get()


@contextmanager
def set_placeholder_style(
    style: PlaceholderStyle,
    parameters: dict[str, DataType],
    parameter_order: list[str] | None = None,
    *,
    infer_parameters: bool = False,
) -> Iterator[PlaceholderConfig]:
    config = PlaceholderConfig(
        style,
        all_parameters=parameters,
        used_parameters={},
        order=[],
        parameter_order=parameter_order or list(parameters),
        infer_parameters=infer_parameters,
    )
    token = _placeholder_config.set(config)
    try:
        yield config
    finally:
        _placeholder_config.reset(token)


def placeholder_sql(generator: Generator, expression: exp.Placeholder) -> str:
    """
    Generate a hex-sl placeholder for an expression like {{foo}} or ${foo}

    Uses {{foo}} or ${foo} for the default mode (depending on kind),
    which can round-trip through parsing.
    But this can be configured to use other modes using the set_placeholder_style
    context manager.
    """
    config = get_placeholder_config()
    name = str(expression.name)
    kind = expression.args.get("kind")

    if kind == PLACEHOLDER_KIND_SEMANTIC:
        return f"${{{name}}}"

    if config is None:
        # Default placeholder mode - round-trip friendly
        return f"{{{{{name}}}}}"
    else:
        # Check if we have the parameter in the list of all parameters
        if name not in config.all_parameters:
            msg = f"Unknown parameter: {name}"
            raise UserFacingError(msg)

        record_order = getattr(generator, PLACEHOLDER_RECORD_ORDER_META, True)
        if record_order:
            config.used_parameters[name] = config.all_parameters[name]

        mode = config.mode

        if mode == PlaceholderStyle.JINJA:
            _record_named_placeholder_occurrence(config, name, record_order)
            return f"{{{{{name}}}}}"
        elif mode in (PlaceholderStyle.NUMERIC, PlaceholderStyle.ASYNCPG):
            # These formats use placeholders with 1-based indices.
            # When there are repititions, the indices should repeat,
            # But only one element per parameter should be added to the
            # order list
            if record_order:
                try:
                    # Find the placeholder in the list
                    i = config.order.index(name)
                except ValueError:
                    # Not found: Add the placeholder to the end of the list
                    i = len(config.order)
                    config.order.append(name)
                config.occurrences.append(name)
            else:
                i = _non_recording_placeholder_index(config, name)

            if mode == PlaceholderStyle.NUMERIC:
                # e.g. SELECT :1
                return f":{i + 1}"
            else:
                # e.g. SELECT $1
                return f"${i + 1}"
        elif mode in (PlaceholderStyle.QMARK, PlaceholderStyle.FORMAT):
            # These formats use positional placeholders, so we always add
            # the placeholder to the end of the order list
            if record_order:
                config.order.append(name)
            i = len(config.order)
            if mode == PlaceholderStyle.QMARK:
                # e.g. SELECT ?
                return f"?{i}"
            else:
                # e.g. SELECT %s
                return f"%s{i}"
        elif mode == PlaceholderStyle.COLON_NAMED:
            # e.g. SELECT :foo
            _record_named_placeholder_occurrence(config, name, record_order)
            return f":{name}"
        elif mode == PlaceholderStyle.DOLLAR_NAMED:
            # e.g. SELECT $foo
            _record_named_placeholder_occurrence(config, name, record_order)
            return f"${name}"
        elif mode == PlaceholderStyle.AT_NAMED:
            # e.g. SELECT @foo
            _record_named_placeholder_occurrence(config, name, record_order)
            return f"@{name}"
        elif mode == PlaceholderStyle.PYFORMAT:
            # e.g. SELECT %(foo)s
            _record_named_placeholder_occurrence(config, name, record_order)
            return f"%({name})s"
        elif mode == PlaceholderStyle.CLICKHOUSE:
            # e.g. SELECT {foo: Int32}
            _record_named_placeholder_occurrence(config, name, record_order)
            dtype = config.all_parameters[name]
            target_type = generator.sql(datatype_to_sqlglot(dtype))
            return f"{{{expression.name}: {target_type}}}"
        else:
            assert_unreachable(mode)
            msg = f"Unsupported placeholder style: {mode}"
            raise ValueError(msg)


def _non_recording_placeholder_index(config: PlaceholderConfig, name: str) -> int:
    try:
        return config.parameter_order.index(name)
    except ValueError:
        return list(config.all_parameters).index(name)


def _record_named_placeholder_occurrence(
    config: PlaceholderConfig,
    name: str,
    record_order: bool,
) -> None:
    if record_order:
        config.occurrences.append(name)


class PlaceholderGeneratorMixin:
    def preprocess(self, expression: exp.Expression) -> exp.Expression:
        previous = getattr(self, PLACEHOLDER_RECORD_ORDER_META, True)
        self.__setattr__(PLACEHOLDER_RECORD_ORDER_META, False)
        try:
            return _super_preprocess(self, expression)
        finally:
            self.__setattr__(PLACEHOLDER_RECORD_ORDER_META, previous)


def _super_preprocess(
    generator: PlaceholderGeneratorMixin,
    expression: exp.Expression,
) -> exp.Expression:
    parent = cast(Any, super(PlaceholderGeneratorMixin, generator))
    return parent.preprocess(expression)


def placeholder_parser_mapping(
    base_parsers: dict[TokenType, Callable[[Parser], exp.Expression | None]],
    *,
    parameter_fallback: Callable[[Parser], exp.Expression | None] | None = None,
) -> dict[TokenType, Callable[[Parser], exp.Expression | None]]:
    return {
        **base_parsers,
        TokenType.PLACEHOLDER: lambda parser: (
            parse_qmark_placeholder(parser)
            or _parse_base_placeholder(parser, base_parsers, TokenType.PLACEHOLDER)
        ),
        TokenType.COLON: lambda parser: (
            parse_colon_placeholder(parser)
            or _parse_base_placeholder(parser, base_parsers, TokenType.COLON)
        ),
        TokenType.MOD: lambda parser: (
            parse_mod_placeholder(parser)
            or _parse_base_placeholder(parser, base_parsers, TokenType.MOD)
        ),
        TokenType.L_BRACE: lambda parser: (
            parse_brace_placeholder(parser)
            or _parse_base_placeholder(parser, base_parsers, TokenType.L_BRACE)
        ),
        TokenType.PARAMETER: lambda parser: parse_parameter_placeholder(
            parser,
            parameter_fallback=parameter_fallback,
            base_fallback=base_parsers.get(TokenType.PARAMETER),
        ),
    }


def parse_qmark_placeholder(parser: Parser) -> exp.Expression | None:
    config = get_placeholder_config()
    if config is None or config.mode != PlaceholderStyle.QMARK:
        return None
    offset = _required_token_offset(parser)
    return _placeholder_for_name(
        parser,
        _next_positional_parameter(config, offset),
        offset=offset,
    )


def parse_colon_placeholder(parser: Parser) -> exp.Expression | None:
    config = get_placeholder_config()
    if config is None:
        return None

    if config.mode == PlaceholderStyle.NUMERIC and parser._match(TokenType.NUMBER):
        return _placeholder_for_name(
            parser,
            _indexed_parameter(config, int(_prev_text(parser))),
        )

    if config.mode == PlaceholderStyle.COLON_NAMED and parser._match_set(
        parser.ID_VAR_TOKENS
    ):
        return _placeholder_for_name(parser, _prev_text(parser))

    return None


def parse_parameter_placeholder(
    parser: Parser,
    *,
    parameter_fallback: Callable[[Parser], exp.Expression | None] | None = None,
    base_fallback: Callable[[Parser], exp.Expression | None] | None = None,
) -> exp.Expression | None:
    token_text = _prev_text(parser)

    if token_text == "$":
        semantic_placeholder = parse_dollar_brace_after_match(parser)
        if semantic_placeholder is not None:
            return semantic_placeholder

        config = get_placeholder_config()
        if config is not None:
            if config.mode == PlaceholderStyle.ASYNCPG and parser._match(
                TokenType.NUMBER
            ):
                return _placeholder_for_name(
                    parser,
                    _indexed_parameter(config, int(_prev_text(parser))),
                )
            if config.mode == PlaceholderStyle.DOLLAR_NAMED and parser._match_set(
                parser.ID_VAR_TOKENS
            ):
                return _placeholder_for_name(parser, _prev_text(parser))

        return parameter_fallback(parser) if parameter_fallback is not None else None

    if token_text == "@":
        config = get_placeholder_config()
        if config is not None and config.mode == PlaceholderStyle.AT_NAMED:
            if parser._match_set(parser.ID_VAR_TOKENS):
                return _placeholder_for_name(parser, _prev_text(parser))
            return None

    return base_fallback(parser) if base_fallback is not None else None


def parse_mod_placeholder(parser: Parser) -> exp.Expression | None:
    config = get_placeholder_config()
    if config is None:
        return None

    index = parser._index
    if config.mode == PlaceholderStyle.FORMAT:
        if parser._match_text_seq("S"):
            offset = _required_token_offset(parser)
            return _placeholder_for_name(
                parser,
                _next_positional_parameter(config, offset),
                offset=offset,
            )
        parser._retreat(index)
        return None

    if config.mode == PlaceholderStyle.PYFORMAT:
        if parser._match(TokenType.L_PAREN):
            name = parser._parse_id_var()
            if (
                name is not None
                and parser._match(TokenType.R_PAREN)
                and parser._match_text_seq("S")
            ):
                return _placeholder_for_name(parser, name.name)
        parser._retreat(index)

    return None


def parse_brace_placeholder(parser: Parser) -> exp.Expression | None:
    config = get_placeholder_config()
    if config is None or config.mode != PlaceholderStyle.CLICKHOUSE:
        return None

    index = parser._index
    name = parser._parse_id_var()
    if name is not None and parser._match(TokenType.COLON):
        kind = parser._parse_types(check_func=False, allow_identifiers=False) or (
            parser._match_text_seq("IDENTIFIER") and "Identifier"
        )
        if kind and parser._match(TokenType.R_BRACE):
            return _placeholder_for_name(parser, name.name)

    parser._retreat(index)
    return None


def _parse_base_placeholder(
    parser: Parser,
    base_parsers: dict[TokenType, Callable[[Parser], exp.Expression | None]],
    token_type: TokenType,
) -> exp.Expression | None:
    base_parser = base_parsers.get(token_type)
    return base_parser(parser) if base_parser is not None else None


def _placeholder_for_name(
    parser: Parser, name: str, *, offset: int | None = None
) -> exp.Expression:
    offset = _required_token_offset(parser) if offset is None else offset
    placeholder = parser.expression(exp.Placeholder, this=exp.to_identifier(name))
    placeholder.meta[PLACEHOLDER_OFFSET_META] = offset

    config = get_placeholder_config()
    if config is not None:
        if name not in config.all_parameters:
            if not config.infer_parameters:
                msg = f"Parameter {name} not found in dataset's parameters"
                raise UserFacingError(msg)
            config.all_parameters[name] = DataType.OTHER
            if name not in config.parameter_order:
                config.parameter_order.append(name)
        config.used_parameters[name] = config.all_parameters[name]
        existing_name = config.parse_occurrences_by_offset.get(offset)
        if existing_name is None:
            config.parse_occurrences_by_offset[offset] = name
            config.order.append(name)
        elif existing_name != name:
            msg = (
                "Placeholder token offset was parsed as multiple parameters: "
                f"{existing_name} and {name}"
            )
            raise ValueError(msg)

    return placeholder


def _prev_text(parser: Parser) -> str:
    if parser._prev is None:
        msg = "Expected previous parser token"
        raise ValueError(msg)
    return parser._prev.text


def _required_token_offset(parser: Parser) -> int:
    """Source offset of the just-matched placeholder token.

    Used to make parse-time placeholder tracking idempotent across sqlglot's
    parser backtracking.
    """
    prev = parser._prev
    offset = getattr(prev, "start", None) if prev is not None else None
    if offset is None:
        msg = "Expected source offset for placeholder token"
        raise ValueError(msg)
    return offset


def _next_positional_parameter(config: PlaceholderConfig, offset: int) -> str:
    # If this exact token offset was already assigned, reuse it. sqlglot
    # re-invokes the placeholder parser for the same `?`/`%s` token while
    # backtracking (e.g. LIMIT parsing), so a monotonic counter would over-count
    # a single placeholder and spuriously raise "missing parameter definition".
    if offset in config.position_by_offset:
        return config.parameter_order[config.position_by_offset[offset]]
    if config.parse_position >= len(config.parameter_order):
        if not config.infer_parameters:
            msg = (
                "Missing parameter definition for positional placeholder "
                f"{config.parse_position + 1}"
            )
            raise UserFacingError(msg)
        name = _inferred_positional_parameter_name(config.parse_position)
        config.parameter_order.append(name)
        config.all_parameters[name] = DataType.OTHER
    index = config.parse_position
    name = config.parameter_order[index]
    config.position_by_offset[offset] = index
    config.parse_position += 1
    return name


def _indexed_parameter(config: PlaceholderConfig, index: int) -> str:
    if index < 1:
        msg = f"Missing parameter definition for positional placeholder {index}"
        raise UserFacingError(msg)
    if index > len(config.parameter_order):
        if not config.infer_parameters:
            msg = f"Missing parameter definition for positional placeholder {index}"
            raise UserFacingError(msg)
        for position in range(len(config.parameter_order), index):
            name = _inferred_positional_parameter_name(position)
            config.parameter_order.append(name)
            config.all_parameters[name] = DataType.OTHER
    return config.parameter_order[index - 1]


def _inferred_positional_parameter_name(index: int) -> str:
    return f"__hexsl_inferred_parameter_{index}"


def parse_jinja_placeholder(parser: Parser) -> exp.Expression | None:
    """
    Parse a jinja-style placeholder expression like {{foo}}.

    This function is used as the _parse_placeholder override for dialects that
    support both {{...}} query parameter placeholders and ${...} semantic
    placeholders. It handles the {{...}} pattern only.

    The ${...} pattern is handled separately by parse_dollar_brace_after_match,
    which is registered in PLACEHOLDER_PARSERS to intercept the $ token.
    """
    parent_type = parser.__class__.__bases__[0]
    if not issubclass(parent_type, Parser):
        msg = (
            f"Argument has type {type(parser)}, expected a subclass "
            "of Parser, but not Parser itself"
        )
        raise TypeError(msg)

    if not parser._match(TokenType.L_BRACE):
        return parent_type._parse_placeholder(parser)

    if not parser._match(TokenType.L_BRACE):
        parser._retreat(1)  # Go back if we don't see a second '{'
        return parent_type._parse_placeholder(parser)

    this = parser._parse_id_var()
    if this is None:
        parser.raise_error("Expecting identifier")
        return None

    if not parser._match(TokenType.R_BRACE):
        parser.raise_error("Expecting }}")
    if not parser._match(TokenType.R_BRACE):
        parser.raise_error("Expecting }}")

    config = get_placeholder_config()
    if config is not None and config.mode == PlaceholderStyle.JINJA:
        return _placeholder_for_name(parser, this.name)

    return parser.expression(exp.Placeholder, this=this)


def parse_dollar_brace_after_match(parser: Parser) -> exp.Expression | None:
    """
    Parse ${...} placeholder after the $ token has already been matched.

    This function is meant to be called from a PLACEHOLDER_PARSERS handler
    after the PARAMETER/DOLLAR token has been matched. It checks if the
    next token is L_BRACE to determine if this is a ${...} pattern.

    Returns:
        - exp.Placeholder with kind=PLACEHOLDER_KIND_SEMANTIC if ${...} pattern is found
        - None if this is not a ${...} pattern (caller should handle fallback)
    """
    # Check if next token is L_BRACE (making this a ${...} pattern)
    if not parser._match(TokenType.L_BRACE):
        # Not a ${...} pattern
        return None

    # We have ${, now collect everything until }
    # The identifier can be: foo, foo.bar, marker, marker.foo, etc.
    parts: list[str] = []

    # Parse the identifier (handles simple identifiers like "foo")
    first_part = parser._parse_id_var()
    if first_part:
        parts.append(first_part.name)

    # Validate that at least one identifier part was parsed
    if not parts:
        parser.raise_error("Expecting identifier after '${'")

    # Check for dot-separated additional parts (e.g., ".bar")
    while parser._match(TokenType.DOT):
        next_part = parser._parse_id_var()
        if next_part:
            parts.append(next_part.name)
        else:
            # Trailing dot without identifier - raise error
            parser.raise_error("Expecting identifier after '.'")

    # Validate depth: only ${col} and ${resource.col} are valid (max 2 parts)
    if len(parts) > 2:
        parser.raise_error(
            f"Invalid placeholder: expected ${{col}} or ${{resource.col}}, "
            f"got ${{{'.'.join(parts)}}}"
        )

    # Closing brace
    if not parser._match(TokenType.R_BRACE):
        parser.raise_error("Expecting }")

    # Join parts with dots to form the full placeholder name
    placeholder_name = ".".join(parts)

    return parser.expression(
        exp.Placeholder, this=placeholder_name, kind=PLACEHOLDER_KIND_SEMANTIC
    )
