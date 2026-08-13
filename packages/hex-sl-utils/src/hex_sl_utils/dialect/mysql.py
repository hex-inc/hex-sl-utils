from __future__ import annotations

import datetime
from collections.abc import Callable
from typing import Any, ClassVar, Literal

from hex_sl_utils._vendor.sqlglot import Generator, exp, tokens, transforms
from hex_sl_utils._vendor.sqlglot.dialects.dialect import rename_func
from hex_sl_utils._vendor.sqlglot.dialects.mysql import MySQL
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
from hex_sl_utils.exception import UnsupportedByDialectError
from hex_sl_utils.expr import ExpressionContext, ExpressionKind, TypedSelectExpression
from hex_sl_utils.time import TimeTruncUnit


class HexSLMySQL(HexSLDialect):
    _TRUNC_FORMATS: ClassVar[dict[str, tuple[str, str]]] = {
        "year": ("%Y-01-01", "DATE"),
        "month": ("%Y-%m-01", "DATE"),
        "day": ("%Y-%m-%d", "DATE"),
        "hour": ("%Y-%m-%d %H:00:00", "DATETIME"),
        "minute": ("%Y-%m-%d %H:%i:00", "DATETIME"),
        "second": ("%Y-%m-%d %H:%i:%s", "DATETIME"),
        "millisecond": ("%Y-%m-%d %H:%i:%s.%f", "DATETIME(3)"),
    }

    @classmethod
    def name(cls) -> DialectName:
        return "mysql"

    @classmethod
    def sqlglot_dialect(cls) -> str:
        return "hex-sl-mysql"

    def truncates_on_integer_division(self) -> bool:
        return False

    def supports_window_partition_by_alias(self) -> bool:
        return False

    def mod_supports_floats(self) -> bool:
        return True

    def supports_median(self) -> bool:
        return False

    def supports_non_finite_floats(self) -> bool:
        return False

    def truncate_cte_name(self, cte_name: str) -> str:
        """
        MySQL has a 64 character limit on table names.

        This includes CTE names used in WITH clauses.
        """
        return cte_name[:64] if len(cte_name) > 64 else cte_name

    def cast_str_to_number(self, arg: TypedSelectExpression) -> TypedSelectExpression:
        """
        Build expression to cast string to number, or null if the string is not a number
        """

        str_as_number = (
            exp.Case()
            .when(
                exp.RegexpLike(
                    this=arg.expression,
                    expression=exp.Literal.string(r"^[-+]?[0-9]*\.?[0-9]+$"),
                ),
                exp.Cast(this=arg.expression, to=exp.DataType.build("DOUBLE")),
            )
            .else_(exp.Null())
        )
        return TypedSelectExpression.from_sqlglot(
            str_as_number,
            DataType.NUMBER,
            arg.kind,
        )

    def cast_str_to_timestamp(
        self, arg: TypedSelectExpression, tz: str, force_tz: bool = False
    ) -> TypedSelectExpression:

        ts_expr = TypedSelectExpression.from_sqlglot(
            exp.cast(arg.expression, to=exp.DataType.build("DATETIME(3)")),
            DataType.TIMESTAMP,
            kind=arg.kind,
        )

        if force_tz:
            return self.at_timezone(ts_expr, tz)
        else:
            return ts_expr

    def compile_literal(
        self,
        literal: Any,
        context: ExpressionContext | None = None,
        data_type: DataType | None = None,
    ) -> TypedSelectExpression:
        """
        Compile a literal expression with MySQL-specific date handling.

        MySQL uses DATE('YYYY-MM-DD') for date literals and TIMESTAMP('string')
        for timestamp literals.
        """

        # Handle datetime objects with MySQL-specific TIMESTAMP function
        if isinstance(literal, datetime.datetime):
            # Convert datetime to string with 'T' separator (to match snapshot
            # expectations)
            dt_str = literal.isoformat()  # Use 'T' separator for MySQL

            # Check if datetime has timezone info
            if literal.tzinfo is not None:
                # This is a timezone-aware datetime (TIMESTAMPTZ)
                # Use TIMESTAMP('datetime_string') for MySQL
                ts_expr = self.func("TIMESTAMP", exp.Literal.string(dt_str))
                result = TypedSelectExpression.from_sqlglot(
                    ts_expr, DataType.TIMESTAMPTZ, ExpressionKind.SCALAR
                )
            else:
                # This is a naive datetime (TIMESTAMP)
                # Use TIMESTAMP('datetime_string') for MySQL
                ts_expr = self.func("TIMESTAMP", exp.Literal.string(dt_str))
                result = TypedSelectExpression.from_sqlglot(
                    ts_expr, DataType.TIMESTAMP, ExpressionKind.SCALAR
                )

            if context is not None:
                result = self.wrap_expression_for_context(result, context)
            return result
        # Handle date objects with MySQL-specific DATE function
        elif isinstance(literal, datetime.date) and not isinstance(
            literal, datetime.datetime
        ):
            # Use DATE('YYYY-MM-DD') for MySQL
            date_str = literal.isoformat()
            date_expr = self.func("DATE", exp.Literal.string(date_str))
            result = TypedSelectExpression.from_sqlglot(
                date_expr, DataType.DATE, ExpressionKind.SCALAR
            )
            if context is not None:
                result = self.wrap_expression_for_context(result, context)
            return result

        # For all other types, use the base implementation
        return super().compile_literal(literal, context, data_type)

    def concat(self, *args: TypedSelectExpression) -> TypedSelectExpression:
        """
        Build a CONCAT expression that treats NULLs as empty strings for MySQL.

        MySQL's CONCAT returns NULL if any argument is NULL, which is different
        from other databases. We use CONCAT_WS with empty separator to get
        consistent behavior.
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
            # Use CONCAT_WS with empty separator - it ignores NULLs
            kind = ExpressionKind._validate_infer_kind([arg.kind for arg in args])
            concat_expr = exp.ConcatWs(
                expressions=[exp.Literal.string("")] + [arg.expression for arg in args]
            )
            return TypedSelectExpression.from_sqlglot(
                concat_expr, DataType.STRING, kind
            )

    def contains(
        self, string: TypedSelectExpression, substring: TypedSelectExpression
    ) -> TypedSelectExpression:
        """
        Build expression to check if a string contains a substring using LOCATE.
        """

        kind = ExpressionKind._validate_infer_kind([string.kind, substring.kind])
        return TypedSelectExpression.from_sqlglot(
            exp.GT(
                this=self.func("LOCATE", substring.expression, string.expression),
                expression=exp.Literal.number(0),
            ),
            kind=kind,
            data_type=DataType.BOOLEAN,
        )

    def datetime_trunc(
        self,
        arg: TypedSelectExpression,
        unit: TimeTruncUnit,
        tz: str,
    ) -> TypedSelectExpression:

        convert_tz = tz if arg.data_type == DataType.TIMESTAMPTZ else None

        if unit == "quarter":
            expression = self._trunc_quarter(arg.expression, convert_tz)
        elif unit == "week" or unit == "weekmonday":
            expression = self._trunc_week(arg.expression, unit, convert_tz)
        elif unit in self._TRUNC_FORMATS:
            format_string, cast_type = self._TRUNC_FORMATS[unit]
            expression = self._trunc_general(
                arg.expression, format_string, cast_type, convert_tz
            )
        else:
            msg = f"Unsupported date_trunc unit: {unit}"
            raise UnsupportedByDialectError(msg)

        if arg.data_type == DataType.TIMESTAMP:
            # Wrap in TIMESTAMP if no timezone is provided
            expression = self.func("TIMESTAMP", expression)
        elif arg.data_type == DataType.DATE:
            expression = exp.Cast(this=expression, to=exp.DataType.build("DATE"))
        elif convert_tz:
            # Convert back to UTC if a timezone was provided
            expression = self.func(
                "CONVERT_TZ",
                expression,
                exp.Literal.string(convert_tz),
                exp.Literal.string("UTC"),
            )

        return TypedSelectExpression.from_sqlglot(
            expression,
            arg.data_type,
            kind=arg.kind,
        )

    def _trunc_general(
        self,
        expr: exp.Expression,
        format_string: str,
        cast_type: str,
        convert_tz: str | None,
    ) -> exp.Expression:
        if convert_tz:
            expr = self.func(
                "CONVERT_TZ",
                expr,
                exp.Literal.string("UTC"),
                exp.Literal.string(convert_tz),
            )

        result: exp.Expression = exp.Cast(
            this=self.func("DATE_FORMAT", expr, exp.Literal.string(format_string)),
            to=exp.DataType.build(cast_type),
        )

        return result

    def _trunc_quarter(
        self, expr: exp.Expression, convert_tz: str | None
    ) -> exp.Expression:
        """
        Implements quarter truncation for MySQL.

        Examples:
        1. Without timezone:
            DATE_TRUNC('quarter', expr) ->
            CAST(
              DATE_FORMAT(
                expr,
                CONCAT(
                  '%Y-',
                  ((QUARTER(expr) - 1) * 3 + 1),
                  '-01',
                )
              ) AS DATE
            )

        2. With timezone:
            DATE_TRUNC('quarter', expr, 'America/New_York') ->
            CONVERT_TZ(
              CAST(DATE_FORMAT(
                CONVERT_TZ(expr, 'UTC', 'America/New_York'),
                CONCAT(
                  '%Y-',
                  (
                    (QUARTER(CONVERT_TZ(expr, 'UTC', 'America/New_York')) - 1) * 3 + 1
                  ),
                  '-01'
                )
              ) AS DATE),
              'America/New_York',
              'UTC'
            )
        """
        # Convert to the specified timezone if provided
        if convert_tz:
            expr = self.func(
                "CONVERT_TZ",
                expr,
                exp.Literal.string("UTC"),
                exp.Literal.string(convert_tz),
            )

        # Build the quarter truncation expression
        quarter_expr: exp.Expression = exp.Cast(
            this=self.func(
                "DATE_FORMAT",
                expr,
                exp.Concat(
                    expressions=[
                        exp.Literal.string("%Y-"),
                        exp.Paren(
                            this=exp.Add(
                                this=exp.Mul(
                                    this=exp.Paren(
                                        this=exp.Sub(
                                            this=self.func("QUARTER", expr),
                                            expression=exp.Literal.number(1),
                                        )
                                    ),
                                    expression=exp.Literal.number(3),
                                ),
                                expression=exp.Literal.number(1),
                            )
                        ),
                        exp.Literal.string("-01"),
                    ]
                ),
            ),
            to=exp.DataType.build("DATE"),
        )

        return quarter_expr

    def _trunc_week(
        self,
        expr: exp.Expression,
        unit: Literal["week", "weekmonday"],
        convert_tz: str | None,
    ) -> exp.Expression:
        """
        Implements week truncation for MySQL, returning a timestamp.

        This function truncates the date to the beginning of the week
        (Sunday or Monday) according to the unit passed.

        Sunday week start examples:
        1. Without timezone:
            DATE_TRUNC('week', expr) ->
            TIMESTAMP(
              DATE_SUB(DATE(expr), INTERVAL DAYOFWEEK(DATE(expr)) - 1 DAY)
            )

        2. With timezone:
            DATE_TRUNC('week', expr, 'America/New_York') ->
            CONVERT_TZ(
              DATE_SUB(
                DATE(CONVERT_TZ(expr, 'UTC', 'America/New_York')),
                INTERVAL
                  DAYOFWEEK(
                    DATE(
                      CONVERT_TZ(expr, 'UTC', 'America/New_York')
                    )
                  ) - 1
                DAY
              ),
              'America/New_York',
              'UTC'
           )

        Monday week start examples:
        1. Without timezone:
            DATE_TRUNC('week', expr) ->
            TIMESTAMP(
              DATE_SUB(DATE(expr), INTERVAL WEEKDAY(DATE(expr)) DAY)
            )

        2. With timezone:
            DATE_TRUNC('week', expr, 'America/New_York') ->
            CONVERT_TZ(
              DATE_SUB(
                DATE(CONVERT_TZ(expr, 'UTC', 'America/New_York')),
                INTERVAL
                  WEEKDAY(
                    DATE(
                      CONVERT_TZ(expr, 'UTC', 'America/New_York')
                    )
                  )
                DAY
              ),
              'America/New_York',
              'UTC'
           )
        """
        # Convert to the specified timezone if provided
        if convert_tz:
            expr = self.func(
                "CONVERT_TZ",
                expr,
                exp.Literal.string("UTC"),
                exp.Literal.string(convert_tz),
            )

        format_string, cast_type = self._TRUNC_FORMATS["day"]
        expression = self._trunc_general(expr, format_string, cast_type, convert_tz)

        # Build the week truncation expression
        if unit == "week":
            week_expr = exp.DateSub(  # type: ignore[no-untyped-call]
                this=self.func("DATE", expression),
                unit=exp.Var(this="DAY"),
                expression=exp.Sub(
                    this=self.func("DAYOFWEEK", self.func("DATE", expr)),
                    expression=exp.Literal.number(1),
                ),
            )
        else:
            week_expr = exp.DateSub(  # type: ignore[no-untyped-call]
                this=self.func("DATE", expression),
                unit=exp.Var(this="DAY"),
                expression=self.func("WEEKDAY", self.func("DATE", expr)),
            )

        return week_expr

    def epoch_ms_to_timestamp(
        self, arg: TypedSelectExpression
    ) -> TypedSelectExpression:
        """
        Build expression to convert epoch milliseconds to a timestamp.
        """

        # from_unixtime(arg / 1000)
        return TypedSelectExpression.from_sqlglot(
            exp.Anonymous(
                this="from_unixtime",
                expressions=[
                    exp.Div(
                        this=exp.paren(arg.expression),
                        expression=exp.Literal.number(1000),
                    ),
                ],
            ),
            DataType.TIMESTAMPTZ,
            kind=arg.kind,
        )

    def day_of_week_part(
        self,
        arg: TypedSelectExpression,
        timezone: str,
    ) -> TypedSelectExpression:
        """
        MySQL-specific day of week implementation.

        MySQL uses DAYOFWEEK(date) which returns Sunday=1, Saturday=7.
        This already matches our expected format, so no adjustment needed.
        """

        if arg.data_type == DataType.TIMESTAMPTZ:
            arg = self.at_timezone(arg, timezone)

        # MySQL DAYOFWEEK(date) returns Sunday=1, Saturday=7 which is what we want
        dow_expr = self.func("DAYOFWEEK", arg.expression)

        return TypedSelectExpression.from_sqlglot(dow_expr, DataType.NUMBER, arg.kind)

    def time_part(
        self,
        arg: TypedSelectExpression,
        unit: Literal["hour", "minute", "second", "millisecond"],
        timezone: str,
    ) -> TypedSelectExpression:

        if arg.data_type == DataType.DATE:
            # Dates don't have a time part, so we return 0
            return self.compile_literal(0)

        if arg.data_type == DataType.TIMESTAMPTZ:
            arg = self.at_timezone(arg, timezone)

        # Use EXTRACT function
        extract_expr: exp.Expression
        if unit == "millisecond":
            # MySQL stores microseconds, so extract microsecond and divide by 1000
            extract_expr = exp.Floor(
                this=exp.Div(
                    this=exp.Extract(
                        this=exp.Identifier(this="microsecond"),
                        expression=arg.expression,
                    ),
                    expression=exp.Literal.number(1000),
                )
            )
        else:
            extract_base = exp.Extract(
                this=exp.Identifier(this=unit.upper()), expression=arg.expression
            )

            # Cast to int for seconds since these are fractional in some dialects
            if unit == "second":
                extract_expr = exp.Cast(
                    this=extract_base, to=exp.DataType.build("BIGINT")
                )
            else:
                extract_expr = extract_base

        return TypedSelectExpression.from_sqlglot(
            extract_expr, DataType.NUMBER, arg.kind
        )

    def at_timezone(self, arg: TypedSelectExpression, tz: str) -> TypedSelectExpression:
        # Clickhouse uses toTimeZone(arg, tz), which returns a timestamp with timezone

        if arg.data_type == DataType.TIMESTAMPTZ:
            return TypedSelectExpression.from_sqlglot(
                exp.cast(
                    self.func(
                        "convert_tz",
                        arg.expression,
                        exp.Literal.string("UTC"),
                        exp.Literal.string(tz),
                    ),
                    to=exp.DataType.build("DATETIME(3)"),
                ),
                DataType.TIMESTAMP,
                kind=arg.kind,
            )
        else:
            return TypedSelectExpression.from_sqlglot(
                exp.cast(
                    self.func(
                        "convert_tz",
                        arg.expression,
                        exp.Literal.string(tz),
                        exp.Literal.string("UTC"),
                    ),
                    to=exp.DataType.build("TIMESTAMP"),
                ),
                DataType.TIMESTAMPTZ,
                kind=arg.kind,
            )

    def splitpart(
        self,
        string: TypedSelectExpression,
        delimiter: TypedSelectExpression,
        part_number: TypedSelectExpression,
    ) -> TypedSelectExpression:
        """
        MySQL does not have a built-in SPLIT function, but it can be replicated
        with some careful use of the SUBSTRING_INDEX function (which can be
        indexed with both positive and negative values) to slice around the
        portion we want to extract.
        """

        kind = ExpressionKind._validate_infer_kind(
            [string.kind, delimiter.kind, part_number.kind]
        )
        return TypedSelectExpression.from_sqlglot(
            exp.Anonymous(
                this="SUBSTRING_INDEX",
                expressions=[
                    exp.Anonymous(
                        this="SUBSTRING_INDEX",
                        expressions=[
                            exp.Concat(
                                expressions=[string.expression, delimiter.expression]
                            ),
                            delimiter.expression,
                            part_number.expression,
                        ],
                    ),
                    delimiter.expression,
                    self.compile_literal(-1).expression,
                ],
            ),
            DataType.STRING,
            kind,
        )


def regexp_like_func() -> Callable[[Generator, exp.Expression], str]:
    return lambda _, e: (
        f"({e.this.sql('hex-sl-mysql')} RLIKE {e.expression.sql('hex-sl-mysql')})"
    )


class HexSlMySQLSqlGlotDialect(MySQL):
    @classmethod
    def dialect_name(cls) -> str:
        return "hex-sl-mysql"

    class Generator(HexSLPlaceholderGeneratorMixin, MySQL.Generator):
        def placeholder_sql(self, expression: exp.Placeholder) -> str:
            return placeholder_sql(self, expression)

        TRANSFORMS = MySQL.Generator.TRANSFORMS.copy() | {
            exp.LogicalOr: rename_func("max"),
            exp.LogicalAnd: rename_func("min"),
            exp.VariancePop: rename_func("var_pop"),
            exp.Variance: rename_func("var_samp"),
            exp.Stddev: rename_func("stddev_pop"),
            exp.StddevPop: rename_func("stddev_pop"),
            exp.StddevSamp: rename_func("stddev_samp"),
            exp.RegexpLike: regexp_like_func(),
            exp.Select: transforms.preprocess(
                [
                    transforms.eliminate_semi_and_anti_joins,
                    hex_sl_eliminate_qualify,
                ]
            ),
        }

    class Tokenizer(MySQL.Tokenizer):
        # Add $ as PARAMETER token so ${...} can be parsed as placeholders
        SINGLE_TOKENS: ClassVar[dict[str, TokenType]] = {
            **tokens.Tokenizer.SINGLE_TOKENS,
            "$": TokenType.PARAMETER,
        }

    class Parser(MySQL.Parser):
        PLACEHOLDER_PARSERS = placeholder_parser_mapping(
            MySQL.Parser.PLACEHOLDER_PARSERS
        )

        def _parse_placeholder(self) -> exp.Expression | None:
            return parse_jinja_placeholder(self)
