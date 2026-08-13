from __future__ import annotations

import datetime
from typing import Any, ClassVar

from hex_sl_utils._vendor.sqlglot import exp, tokens, transforms
from hex_sl_utils._vendor.sqlglot.dialects.trino import Trino
from hex_sl_utils._vendor.sqlglot.tokens import TokenType
from hex_sl_utils.datatype import DataType
from hex_sl_utils.dialect.dialect import HexSLDialect
from hex_sl_utils.dialect.dialect_name import DialectName
from hex_sl_utils.dialect.placeholder import (
    HexSLPlaceholderGeneratorMixin,
    parse_jinja_placeholder,
    placeholder_parser_mapping,
    placeholder_sql,
)
from hex_sl_utils.dialect.transforms import hex_sl_eliminate_qualify
from hex_sl_utils.expr import ExpressionContext, ExpressionKind, TypedSelectExpression
from hex_sl_utils.time import TimeTruncUnit


class HexSLTrino(HexSLDialect):
    @classmethod
    def name(cls) -> DialectName:
        return "trino"

    @classmethod
    def sqlglot_dialect(cls) -> str:
        return "hex-sl-trino"

    def supports_window_partition_by_alias(self) -> bool:
        return False

    def truncates_on_integer_division(self) -> bool:
        return True

    def mod_supports_floats(self) -> bool:
        return True

    def supports_median(self) -> bool:
        return False

    def supports_percentile_approx(self) -> bool:
        return True

    def build_percentile_approx(
        self,
        arg: TypedSelectExpression,
        percentile: float,
    ) -> TypedSelectExpression:

        cast_typed = self.cast_to_float(arg)
        percentile_expr = exp.ApproxQuantile(
            this=cast_typed.expression, quantile=exp.Literal.number(percentile)
        )

        return TypedSelectExpression.from_sqlglot(
            percentile_expr, DataType.NUMBER, arg.kind
        )

    def supports_non_finite_floats(self) -> bool:
        return True

    def build_isnan(self, arg: TypedSelectExpression) -> TypedSelectExpression:
        """
        Build an IS NAN check using Trino's native is_nan function.
        """

        # Use Trino's native is_nan function
        cast_arg = self.cast_to_float(arg)
        isnan_expr = self.func("is_nan", cast_arg.expression)

        return TypedSelectExpression.from_sqlglot(
            isnan_expr, DataType.BOOLEAN, arg.kind
        )

    def supports_cot_function(self) -> bool:
        return False

    def supports_microseconds_in_timestamps(self) -> bool:
        """
        Returns whether the dialect supports fractional seconds in timestamps.

        Trino supports these, but our implementation does not.
        """
        return False

    def clamp_left_right_to_str_length(self) -> bool:
        return True

    def epoch_ms_to_timestamp(
        self,
        arg: TypedSelectExpression,
    ) -> TypedSelectExpression:

        # port of prior ibis logic, in which we first calculate at a
        # second-level precision, and then add the milliseconds back separately
        # (potentially to avoid overflow? unknown why ibis chose this approach)
        naive_seconds_ts = exp.Anonymous(
            this="FROM_UNIXTIME",
            expressions=[
                exp.Floor(
                    this=exp.Div(
                        this=exp.Cast(
                            this=exp.Cast(
                                this=arg.expression, to=exp.DataType.build("BIGINT")
                            ),
                            to=exp.DataType.build("DOUBLE"),
                        ),
                        expression=exp.Literal.number(1000),
                    )
                )
            ],
        )

        # Use microseconds instead of milliseconds to avoid rounding errors
        millils_part = exp.paren(
            exp.Mod(this=exp.paren(arg.expression), expression=exp.Literal.number(1000))
        )

        naive_ts = TypedSelectExpression.from_sqlglot(
            exp.DateAdd(  # type: ignore[no-untyped-call]
                this=exp.cast(naive_seconds_ts, to=exp.DataType.Type.TIMESTAMP),
                unit=exp.Literal.string("millisecond"),
                expression=millils_part,
            ),
            DataType.TIMESTAMP,
            kind=arg.kind,
        )

        return self.at_timezone(naive_ts, "UTC")

    def datetime_to_epoch_ms(self, arg: TypedSelectExpression) -> TypedSelectExpression:
        """
        Build expression to convert a timestamp to epoch milliseconds.

        Trino uses TO_UNIXTIME() to get epoch seconds.
        """

        if arg.data_type == DataType.TIMESTAMPTZ:
            # Always convert to UTC before extracting epoch millis
            arg = self.at_timezone(arg, "UTC")

        # Use TO_UNIXTIME() to get epoch seconds, then multiply by 1000 and floor
        epoch_seconds = self.func("TO_UNIXTIME", arg.expression)

        # Multiply by 1000 to get milliseconds
        epoch_ms = exp.Mul(this=epoch_seconds, expression=exp.Literal.number(1000))

        # Floor the result and cast to BIGINT (matching expected baseline pattern)
        floored = exp.Floor(this=epoch_ms)
        casted = exp.Cast(this=floored, to=exp.DataType.build("BIGINT"))

        return TypedSelectExpression.from_sqlglot(casted, DataType.NUMBER, arg.kind)

    def datetime_trunc(
        self,
        arg: TypedSelectExpression,
        unit: TimeTruncUnit,
        tz: str,
    ) -> TypedSelectExpression:

        convert_tz = tz if arg.data_type == DataType.TIMESTAMPTZ else None

        # Apply timezone if provided, otherwise use the original expression
        tz_expression = (
            exp.AtTimeZone(this=arg.expression, zone=exp.Literal.string(convert_tz))
            if convert_tz is not None
            else arg.expression
        )

        expression: exp.Expression
        if unit == "week":
            # Special case for week: Truncate week to Sunday rather than Monday
            expression = exp.DateAdd(  # type: ignore[no-untyped-call]
                this=exp.DateTrunc(  # type: ignore[no-untyped-call]
                    unit=exp.Literal.string("week"),
                    this=exp.DateAdd(  # type: ignore[no-untyped-call]
                        this=tz_expression,
                        unit=exp.Literal.string("day"),
                        expression=exp.Literal.number(1),
                    ),
                ),
                unit=exp.Literal.string("day"),
                expression=exp.Literal.number(-1),
            )
        else:
            # For all other units
            sql_unit = "week" if unit == "weekmonday" else unit
            expression = exp.DateTrunc(  # type: ignore[no-untyped-call]
                unit=exp.Literal.string(sql_unit.upper()), this=tz_expression
            )

        if arg.data_type == DataType.DATE:
            expression = exp.Cast(this=expression, to=exp.DataType.build("DATE"))

        return TypedSelectExpression.from_sqlglot(
            expression, arg.data_type, kind=arg.kind
        )

    def timestamp_subsecond_suffix(self) -> str | None:
        return ".000"

    def day_of_week_part(
        self,
        arg: TypedSelectExpression,
        timezone: str,
    ) -> TypedSelectExpression:
        """
        Trino-specific day of week implementation.

        Trino uses DAY_OF_WEEK(date) which returns Monday=1, Sunday=7.
        We need to adjust this to get Sunday=1, Saturday=7.
        Formula: CASE WHEN DAY_OF_WEEK(date) = 7 THEN 1 ELSE DAY_OF_WEEK(date) + 1 END
        """

        if arg.data_type == DataType.TIMESTAMPTZ:
            arg = self.at_timezone(arg, timezone)

        # Trino DAY_OF_WEEK returns Monday=1, Sunday=7
        # We need Sunday=1, Saturday=7, so we use: DAY_OF_WEEK % 7 + 1
        dow_expr = self.func("DAY_OF_WEEK", arg.expression)
        adjusted_dow = exp.Add(
            this=exp.Mod(this=dow_expr, expression=exp.Literal.number(7)),
            expression=exp.Literal.number(1),
        )

        return TypedSelectExpression.from_sqlglot(
            adjusted_dow, DataType.NUMBER, arg.kind
        )

    def at_timezone(self, arg: TypedSelectExpression, tz: str) -> TypedSelectExpression:

        if arg.data_type == DataType.TIMESTAMPTZ:
            return TypedSelectExpression.from_sqlglot(
                self.func("at_timezone", arg.expression, exp.Literal.string(tz)),
                DataType.TIMESTAMP,
                kind=arg.kind,
            )
        else:
            return TypedSelectExpression.from_sqlglot(
                self.func("with_timezone", arg.expression, exp.Literal.string(tz)),
                DataType.TIMESTAMPTZ,
                kind=arg.kind,
            )

    def time_part(
        self,
        arg: TypedSelectExpression,
        unit: str,
        timezone: str,
    ) -> TypedSelectExpression:

        if arg.data_type == DataType.DATE:
            # Dates don't have a time part, so we return 0
            return self.compile_literal(0)

        if arg.data_type == DataType.TIMESTAMPTZ:
            arg = self.at_timezone(arg, timezone)

        # Use EXTRACT function or MILLISECOND function
        if unit == "millisecond":
            # Trino has a native MILLISECOND function
            extract_expr = self.func("MILLISECOND", arg.expression)
        else:
            extract_expr = exp.Extract(
                this=exp.Identifier(this=unit.upper()), expression=arg.expression
            )

            # Cast to int for seconds since these are fractional in some dialects
            if unit == "second":
                extract_expr = exp.Cast(
                    this=extract_expr, to=exp.DataType.build("BIGINT")
                )

        return TypedSelectExpression.from_sqlglot(
            extract_expr, DataType.NUMBER, arg.kind
        )

    def startswith(
        self, string: TypedSelectExpression, prefix: TypedSelectExpression
    ) -> TypedSelectExpression:
        """
        Trino-specific startswith implementation using native STARTS_WITH function.
        """

        kind = ExpressionKind._validate_infer_kind([string.kind, prefix.kind])
        startswith_expr = self.func("STARTS_WITH", string.expression, prefix.expression)
        return TypedSelectExpression.from_sqlglot(
            startswith_expr, DataType.BOOLEAN, kind
        )

    def endswith(
        self, string: TypedSelectExpression, suffix: TypedSelectExpression
    ) -> TypedSelectExpression:
        """
        Trino-specific endswith implementation using SUBSTR with negative index.
        """

        kind = ExpressionKind._validate_infer_kind([string.kind, suffix.kind])
        # Use SUBSTR with negative index: SUBSTR(string, -LENGTH(suffix)) = suffix
        suffix_length = exp.Length(this=suffix.expression)
        neg_length = exp.Neg(this=suffix_length)
        substr_expr = self.func("SUBSTR", string.expression, neg_length)
        eq_expr = exp.EQ(this=substr_expr, expression=suffix.expression)
        return TypedSelectExpression.from_sqlglot(eq_expr, DataType.BOOLEAN, kind)

    def concat(self, *args: TypedSelectExpression) -> TypedSelectExpression:
        """
        Build a CONCAT expression that treats NULLs as empty strings for Trino.

        Trino's CONCAT returns NULL if any argument is NULL, so we need to wrap
        each argument in COALESCE to ensure consistent behavior.
        """

        if len(args) == 0:
            return self.compile_literal("")
        elif len(args) == 1:
            # For single argument, wrap in COALESCE to handle NULL
            return TypedSelectExpression.from_sqlglot(
                exp.Coalesce(
                    this=args[0].expression, expressions=[exp.Literal.string("")]
                ),
                DataType.STRING,
                args[0].kind,
            )
        else:
            # Wrap each argument in COALESCE to convert NULL to empty string
            kind = ExpressionKind._validate_infer_kind([arg.kind for arg in args])
            coalesced_args = [
                exp.Coalesce(this=arg.expression, expressions=[exp.Literal.string("")])
                for arg in args
            ]
            concat_expr = exp.Concat(expressions=coalesced_args)
            return TypedSelectExpression.from_sqlglot(
                concat_expr, DataType.STRING, kind
            )

    def splitpart(
        self,
        string: TypedSelectExpression,
        delimiter: TypedSelectExpression,
        part_number: TypedSelectExpression,
    ) -> TypedSelectExpression:
        """
        Trino-specific splitpart implementation using native SPLIT_PART function.

        Trino's SPLIT_PART returns null for out-of-bounds indices, so we coalesce
        to empty string only for non-null input strings.
        """

        kind = ExpressionKind._validate_infer_kind(
            [string.kind, delimiter.kind, part_number.kind]
        )

        # Use Trino's native SPLIT_PART function
        split_part_expr = self.func(
            "SPLIT_PART",
            string.expression,
            delimiter.expression,
            part_number.expression,
        )

        # Coalesce null results (out-of-bounds) to empty string, but only for
        # non-null input
        coalesce_expr = exp.Coalesce(
            this=split_part_expr, expressions=[exp.Literal.string("")]
        )

        # Handle null string case with IF - return null if input string is null
        result_expr = exp.If(
            this=exp.Is(this=string.expression, expression=exp.Null()),
            true=exp.Null(),
            false=coalesce_expr,
        )

        return TypedSelectExpression.from_sqlglot(result_expr, DataType.STRING, kind)

    def compile_literal(
        self,
        literal: Any,
        context: ExpressionContext | None = None,
        data_type: DataType | None = None,
    ) -> TypedSelectExpression:
        """
        Compile a literal expression with proper type handling for Trino.

        Trino uses FROM_ISO8601_TIMESTAMP for ISO timestamp strings.
        """
        # Handle date and datetime objects with Trino-specific functions

        if isinstance(literal, datetime.datetime):
            # Check if datetime has timezone info
            if literal.tzinfo is not None:
                # This is a timezone-aware datetime (TIMESTAMPTZ)
                # Trino uses FROM_ISO8601_TIMESTAMP for ISO format strings
                dt_str = literal.isoformat()
                ts_expr = exp.Cast(
                    this=self.func(
                        "FROM_ISO8601_TIMESTAMP", exp.Literal.string(dt_str)
                    ),
                    to=exp.DataType.build("TIMESTAMP WITH TIME ZONE"),
                )
                result = TypedSelectExpression.from_sqlglot(
                    ts_expr, DataType.TIMESTAMPTZ, ExpressionKind.SCALAR
                )
            else:
                # This is a naive datetime (TIMESTAMP)
                # Trino uses FROM_ISO8601_TIMESTAMP for ISO format
                dt_str = literal.isoformat()
                ts_expr = exp.Cast(
                    this=self.func(
                        "FROM_ISO8601_TIMESTAMP", exp.Literal.string(dt_str)
                    ),
                    to=exp.DataType.build("TIMESTAMP"),
                )
                result = TypedSelectExpression.from_sqlglot(
                    ts_expr, DataType.TIMESTAMP, ExpressionKind.SCALAR
                )
            if context is not None:
                result = self.wrap_expression_for_context(result, context)
            return result
        # Handle date objects with Trino-specific FROM_ISO8601_DATE function
        elif isinstance(literal, datetime.date) and not isinstance(
            literal, datetime.datetime
        ):
            # Use FROM_ISO8601_DATE('YYYY-MM-DD') for Trino
            date_str = literal.isoformat()
            date_expr = self.func("FROM_ISO8601_DATE", exp.Literal.string(date_str))
            result = TypedSelectExpression.from_sqlglot(
                date_expr, DataType.DATE, ExpressionKind.SCALAR
            )

            if context is not None:
                result = self.wrap_expression_for_context(result, context)
            return result

        # For all other types, use the base implementation
        return super().compile_literal(literal, context, data_type)


def custom_epoch_cast_to_ts(expression: exp.Expression) -> exp.Expression:
    """
    Reimplementation of the default sqlglot implementation that handles
    expression.name as an exp.Identifier

    Replace 'epoch' in casts by the equivalent date literal.
    """
    if (
        isinstance(expression, (exp.Cast, exp.TryCast))
        and str(expression.name).lower() == "epoch"
        and expression.to.this in exp.DataType.TEMPORAL_TYPES
    ):
        expression.this.replace(exp.Literal.string("1970-01-01 00:00:00"))

    return expression


class HexSlTrinoSqlGlotDialect(Trino):
    SUPPORTS_USER_DEFINED_TYPES = True

    @classmethod
    def dialect_name(cls) -> str:
        return "hex-sl-trino"

    class Generator(HexSLPlaceholderGeneratorMixin, Trino.Generator):
        TRANSFORMS = Trino.Generator.TRANSFORMS.copy() | {
            exp.Select: transforms.preprocess(
                [
                    transforms.eliminate_semi_and_anti_joins,
                    hex_sl_eliminate_qualify,
                ]
            ),
            exp.Cast: transforms.preprocess([custom_epoch_cast_to_ts]),
            exp.TryCast: transforms.preprocess([custom_epoch_cast_to_ts]),
        }

        def placeholder_sql(self, expression: exp.Placeholder) -> str:
            return placeholder_sql(self, expression)

    class Tokenizer(Trino.Tokenizer):
        # Add $ as PARAMETER token so ${...} can be parsed as placeholders
        SINGLE_TOKENS: ClassVar[dict[str, TokenType]] = {
            **tokens.Tokenizer.SINGLE_TOKENS,
            "$": TokenType.PARAMETER,
        }

    class Parser(Trino.Parser):
        PLACEHOLDER_PARSERS = placeholder_parser_mapping(
            Trino.Parser.PLACEHOLDER_PARSERS
        )

        def _parse_placeholder(self) -> exp.Expression | None:
            return parse_jinja_placeholder(self)
