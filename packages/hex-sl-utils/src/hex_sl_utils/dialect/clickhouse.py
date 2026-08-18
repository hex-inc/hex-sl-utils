from __future__ import annotations

import datetime
from typing import Any, ClassVar

from hex_sl_utils._vendor.sqlglot import exp, tokens
from hex_sl_utils._vendor.sqlglot.dialects.clickhouse import (
    ClickHouse as SqlGlotClickHouse,
)
from hex_sl_utils._vendor.sqlglot.dialects.dialect import (
    NormalizationStrategy,
    rename_func,
)
from hex_sl_utils._vendor.sqlglot.tokens import TokenType
from hex_sl_utils.datatype import DataType
from hex_sl_utils.dialect.dialect import Dialect
from hex_sl_utils.dialect.dialect_name import DialectName
from hex_sl_utils.dialect.placeholder import (
    PlaceholderGeneratorMixin,
    parse_jinja_placeholder,
    placeholder_parser_mapping,
    placeholder_sql,
)
from hex_sl_utils.expr import ExpressionContext, ExpressionKind, TypedSelectExpression
from hex_sl_utils.time import TimeTruncUnit


class ClickHouse(Dialect):
    @classmethod
    def name(cls) -> DialectName:
        return "clickhouse"

    @classmethod
    def sqlglot_dialect(cls) -> str:
        return "hex-sl-clickhouse"

    def truncates_on_integer_division(self) -> bool:
        return False

    def mod_supports_floats(self) -> bool:
        return True

    def supports_inequality_joins(self) -> bool:
        return False

    def supports_median(self) -> bool:
        return True

    def supports_percentile_exact(self) -> bool:
        return True

    def supports_percentile_approx(self) -> bool:
        return True

    def build_percentile_exact(
        self,
        arg: TypedSelectExpression,
        percentile: float,
    ) -> TypedSelectExpression:
        cast_typed = self.cast_to_float(arg)
        percentile_expr = exp.ParameterizedAgg(
            this="quantileExact",
            expressions=[exp.Literal.number(percentile)],
            params=[cast_typed.expression],
        )
        return TypedSelectExpression.from_sqlglot(
            percentile_expr, DataType.NUMBER, arg.kind
        )

    def build_percentile_approx(
        self,
        arg: TypedSelectExpression,
        percentile: float,
    ) -> TypedSelectExpression:
        cast_typed = self.cast_to_float(arg)
        percentile_expr = exp.ParameterizedAgg(
            this="quantileTDigest",
            expressions=[exp.Literal.number(percentile)],
            params=[cast_typed.expression],
        )
        return TypedSelectExpression.from_sqlglot(
            percentile_expr, DataType.NUMBER, arg.kind
        )

    def supports_non_finite_floats(self) -> bool:
        return True

    def supports_cot_function(self) -> bool:
        return False

    def build_isnan(self, arg: TypedSelectExpression) -> TypedSelectExpression:
        """
        Build an IS NAN check using ClickHouse's native isNaN function.
        """

        # Use ClickHouse's native isNaN function
        cast_arg = self.cast_to_float(arg)
        isnan_expr = self.func("isNaN", cast_arg.expression)

        return TypedSelectExpression.from_sqlglot(
            isnan_expr, DataType.BOOLEAN, arg.kind
        )

    def build_median(self, arg: TypedSelectExpression) -> TypedSelectExpression:
        """
        Build a MEDIAN expression for ClickHouse.

        ClickHouse uses lowercase 'median' function which is an alias for quantile(0.5).
        """

        # Cast to float using dialect method
        cast_typed = self.cast_to_float(arg)

        # Use lowercase 'median' function (alias for quantile(0.5))
        median_expr = self.func("median", cast_typed.expression)

        return TypedSelectExpression.from_sqlglot(
            median_expr, DataType.NUMBER, arg.kind
        )

    def join_condition_matches_nulls(
        self, lhs: exp.Expression, rhs: exp.Expression
    ) -> exp.Expression:
        """
        Build the join ON condition that matches nulls.

        Clickhouse doesn't like OR conditions in the join ON clause, instead use
        isNotDistinctFrom()
        """
        return self.func(
            "isNotDistinctFrom",
            lhs,
            rhs,
        )

    def epoch_ms_to_timestamp(
        self, arg: TypedSelectExpression
    ) -> TypedSelectExpression:
        """
        Build expression to convert epoch milliseconds to a timestamp.
        """

        # toDateTime64(arg / 1000, 3, 'UTC')
        return TypedSelectExpression.from_sqlglot(
            exp.Anonymous(
                this="toDateTime64",
                expressions=[
                    exp.Div(
                        this=exp.paren(arg.expression),
                        expression=exp.Literal.number(1000),
                    ),
                    exp.Literal.number(3),
                    exp.Literal.string("UTC"),
                ],
            ),
            DataType.TIMESTAMPTZ,
            kind=arg.kind,
        )

    def datetime_to_epoch_ms(self, arg: TypedSelectExpression) -> TypedSelectExpression:
        """
        Build expression to convert a timestamp to epoch milliseconds.
        """

        expr_arg: exp.Expression
        if arg.data_type == DataType.DATE:
            # toRelativeSecondNum(arg) * 1000 for dates
            expr_arg = exp.Mul(
                this=exp.Anonymous(
                    this="toRelativeSecondNum", expressions=[arg.expression]
                ),
                expression=exp.Literal.number(1000),
            )
        else:
            # For timestamps, use toUnixTimestamp64Milli which works with
            # DateTime64 types
            # Wrap the entire expression in parentheses for proper precedence in
            # arithmetic operations
            expr_arg = exp.Paren(
                this=self.func("toUnixTimestamp64Milli", arg.expression)
            )

        return TypedSelectExpression.from_sqlglot(
            expr_arg,
            DataType.NUMBER,
            kind=arg.kind,
        )

    def cast_str_to_timestamp(
        self, arg: TypedSelectExpression, tz: str, force_tz: bool = False
    ) -> TypedSelectExpression:
        return TypedSelectExpression.from_sqlglot(
            self.func(
                "parseDateTime64BestEffortOrNull",
                arg.expression,
                exp.Literal.number(3),
                exp.Literal.string(tz),
            ),
            DataType.TIMESTAMPTZ,
            kind=arg.kind,
        )

    def cast_str_to_number(self, arg: TypedSelectExpression) -> TypedSelectExpression:
        """
        Build expression to cast string to number, or null if the string is
        not a number
        """

        # Use accurateCastOrNull for ClickHouse
        cast_expr = exp.Anonymous(
            this="accurateCastOrNull",
            expressions=[arg.expression, exp.Literal.string("Nullable(Float64)")],
        )
        return TypedSelectExpression.from_sqlglot(cast_expr, DataType.NUMBER, arg.kind)

    def cast_str_to_date(self, arg: TypedSelectExpression) -> TypedSelectExpression:
        """
        Build expression to cast string to date, or null if the string is
        not a date
        """

        # Use accurateCastOrNull for ClickHouse
        cast_expr = exp.Anonymous(
            this="accurateCastOrNull",
            expressions=[arg.expression, exp.Literal.string("Nullable(DATE)")],
        )
        return TypedSelectExpression.from_sqlglot(cast_expr, DataType.DATE, arg.kind)

    def cast_timestamptz_to_date(
        self, arg: TypedSelectExpression, tz: str
    ) -> TypedSelectExpression:
        """
        Build expression to cast timestamptz to date with ClickHouse nullable handling.
        """

        # Convert to target timezone first
        tz_arg = self.at_timezone(arg, tz)
        # ClickHouse needs Nullable type for cast
        nullable_date = exp.DataType(this=exp.DataType.Type.DATE, nullable=True)
        cast_expr = exp.Cast(this=tz_arg.expression, to=nullable_date)
        return TypedSelectExpression.from_sqlglot(cast_expr, DataType.DATE, arg.kind)

    def cast_timestamp_to_date(
        self, arg: TypedSelectExpression
    ) -> TypedSelectExpression:
        """
        Build expression to cast timestamp to date with ClickHouse nullable handling.
        """

        # ClickHouse needs Nullable type for cast
        nullable_date = exp.DataType(this=exp.DataType.Type.DATE, nullable=True)
        cast_expr = exp.Cast(this=arg.expression, to=nullable_date)
        return TypedSelectExpression.from_sqlglot(cast_expr, DataType.DATE, arg.kind)

    def cast_to_float(self, arg: TypedSelectExpression) -> TypedSelectExpression:
        """
        Cast to float always uses Nullable(Float64) in ClickHouse.
        """

        # Always use Nullable(Float64) for ClickHouse
        # Create a DataType node with nested structure for Nullable(Float64)
        nullable_float = exp.DataType(this=exp.DataType.Type.DOUBLE, nullable=True)

        cast_expr = exp.Cast(this=arg.expression, to=nullable_float)
        return TypedSelectExpression.from_sqlglot(cast_expr, DataType.NUMBER, arg.kind)

    def cast_to_int(self, arg: TypedSelectExpression) -> TypedSelectExpression:
        """
        Cast to int always uses Nullable(Int32) in ClickHouse.
        """

        # Always use Nullable(Int32) for ClickHouse
        # Create a DataType node with nested structure for Nullable(Int32)
        nullable_int = exp.DataType(this=exp.DataType.Type.INT, nullable=True)

        cast_expr = exp.Cast(this=arg.expression, to=nullable_int)
        return TypedSelectExpression.from_sqlglot(cast_expr, DataType.NUMBER, arg.kind)

    def cast_to_string(self, arg: TypedSelectExpression) -> TypedSelectExpression:
        """
        Cast to string always uses Nullable(String) in ClickHouse.
        """

        # Always use Nullable(String) for ClickHouse
        # Create a DataType node with nested structure for Nullable(String)
        nullable_string = exp.DataType(this=exp.DataType.Type.VARCHAR, nullable=True)

        cast_expr = exp.Cast(this=arg.expression, to=nullable_string)
        return TypedSelectExpression.from_sqlglot(cast_expr, DataType.STRING, arg.kind)

    def compile_literal(
        self,
        literal: Any,
        context: ExpressionContext | None = None,
        data_type: DataType | None = None,
    ) -> TypedSelectExpression:
        """
        Compile a literal expression with proper type handling for ClickHouse.

        ClickHouse uses parseDateTimeBestEffort for timestamps.
        """
        # Handle datetime objects with ClickHouse-specific functions

        if isinstance(literal, datetime.datetime):
            # Check if datetime has timezone info
            if literal.tzinfo is not None:
                # This is a timezone-aware datetime (TIMESTAMPTZ)
                # ClickHouse uses parseDateTime64BestEffort for DateTime64
                # Use isoformat() to get 'T' separator and proper +00:00 format
                dt_str = literal.isoformat()
                ts_expr = self.func(
                    "parseDateTime64BestEffort",
                    exp.Literal.string(dt_str),
                    exp.Literal.number(3),  # 3 decimal places for milliseconds
                )
                result = TypedSelectExpression.from_sqlglot(
                    ts_expr, DataType.TIMESTAMPTZ, ExpressionKind.SCALAR
                )
            else:
                # This is a naive datetime (TIMESTAMP)
                # ClickHouse uses parseDateTime64BestEffort for DateTime64
                # Use isoformat() to get 'T' separator
                dt_str = literal.isoformat()
                ts_expr = self.func(
                    "parseDateTime64BestEffort",
                    exp.Literal.string(dt_str),
                    exp.Literal.number(3),  # 3 decimal places for milliseconds
                )
                result = TypedSelectExpression.from_sqlglot(
                    ts_expr, DataType.TIMESTAMP, ExpressionKind.SCALAR
                )

            if context is not None:
                result = self.wrap_expression_for_context(result, context)
            return result

        # Handle date objects with ClickHouse-specific toDate function
        elif isinstance(literal, datetime.date) and not isinstance(
            literal, datetime.datetime
        ):
            # Use toDate('YYYY-MM-DD') for ClickHouse
            date_str = literal.isoformat()
            date_expr = self.func("toDate", exp.Literal.string(date_str))
            result = TypedSelectExpression.from_sqlglot(
                date_expr, DataType.DATE, ExpressionKind.SCALAR
            )
            if context is not None:
                result = self.wrap_expression_for_context(result, context)
            return result

        # For all other types, use the base implementation
        return super().compile_literal(literal, context, data_type)

    def datetime_trunc(
        self,
        arg: TypedSelectExpression,
        unit: TimeTruncUnit,
        tz: str,
    ) -> TypedSelectExpression:
        convert_tz = tz if arg.data_type == DataType.TIMESTAMPTZ else None

        if unit.lower() == "week":
            result_expr = self._trunc_week(arg.expression, convert_tz)
        else:
            sql_unit = "week" if unit.lower() == "weekmonday" else unit
            result_expr = self._trunc_general(arg.expression, sql_unit, convert_tz)

        if arg.data_type == DataType.DATE:
            # Preserve input DATE type
            result_expr = self.func("toDate", result_expr)
        elif unit in self._DATE_UNITS:
            # make sure to return a timestamp if the input is not a date,
            # but truncation was a date unit
            if convert_tz is not None:
                result_expr = self.func(
                    "toDateTime64",
                    result_expr,
                    exp.Literal.number(3),
                    exp.Literal.string(tz),
                )
            else:
                result_expr = self.func(
                    "toDateTime64", result_expr, exp.Literal.number(3)
                )

        return TypedSelectExpression.from_sqlglot(
            result_expr,
            DataType.TIMESTAMPTZ if convert_tz is not None else DataType.TIMESTAMP,
            kind=arg.kind,
        )

    def _trunc_general(
        self,
        expr: exp.Expression,
        unit: TimeTruncUnit,
        convert_tz: str | None,
    ) -> exp.Expression:
        """
        Implements general date truncation for ClickHouse.

        Uses ClickHouse's DATE_TRUNC function and handles timezone when provided.
        For units larger than a day, the result is cast to a timestamp for consistency.

        Args:
            expr: The expression to be truncated.
            unit: The unit to truncate to (e.g., 'year', 'month', 'day', 'hour', etc.).
            convert_tz: The timezone to be used for the truncation, if any.

        Returns:
            exp.Expression: A new expression representing the truncated date/time
                           as a timestamp.
        """

        truncated_expr = self.func(
            "dateTrunc",
            exp.Literal.string(unit),
            expr,
            *([] if convert_tz is None else [exp.Literal.string(convert_tz)]),
        )

        return truncated_expr

    def _trunc_week(
        self,
        expr: exp.Expression,
        convert_tz: str | None,
    ) -> exp.Expression:
        """
        Implements week truncation for ClickHouse, always truncating to Sunday.

        This method adjusts the default Monday-based week truncation in ClickHouse
        to be Sunday-based. The result is also cast to a timestamp for consistency.

        The generated SQL will look like this:
        toDateTime64(
            DATE_TRUNC(
                'week',
                expr + INTERVAL 1 day,
                [timezone]
            ) - INTERVAL 1 day
        )

        Args:
            expr: The expression representing the date to be truncated.
            convert_tz: The timezone to be used for the truncation, if any.

        Returns:
            exp.Expression: A new expression representing the date truncated to
                            the start of the week (Sunday), as a timestamp.
        """
        # Add 1 day
        adjusted_expr: exp.Expression = exp.Add(
            this=expr,
            expression=exp.Interval(this=exp.Literal.number(1), unit="day"),  # type: ignore[no-untyped-call]
        )

        # Truncate to week
        truncated_expr = self.func(
            "dateTrunc",
            exp.Literal.string("week"),
            adjusted_expr,
            *([] if convert_tz is None else [exp.Literal.string(convert_tz)]),
        )

        # Subtract 1 day
        result_expr: exp.Expression = exp.Sub(
            this=truncated_expr,
            expression=exp.Interval(this=exp.Literal.number(1), unit="day"),  # type: ignore[no-untyped-call]
        )

        return result_expr

    def now(self, timezone: str) -> TypedSelectExpression:
        return self.at_timezone(super().now(timezone), timezone)

    def at_timezone(self, arg: TypedSelectExpression, tz: str) -> TypedSelectExpression:
        # Clickhouse uses toTimeZone(arg, tz), which returns a timestamp with timezone

        return TypedSelectExpression.from_sqlglot(
            exp.Anonymous(
                this="toTimeZone",
                expressions=[
                    arg.expression,
                    exp.Literal.string(tz),
                ],
            ),
            DataType.TIMESTAMPTZ,
            kind=arg.kind,
        )

    def cast_date_to_timestamp(
        self, arg: TypedSelectExpression
    ) -> TypedSelectExpression:
        """
        Build expression to cast a date to a naive timestamp.
        Use toDateTime64 to handle NULLs properly in ClickHouse.
        """

        return TypedSelectExpression.from_sqlglot(
            exp.Anonymous(
                this="toDateTime64",
                expressions=[arg.expression, exp.Literal.number(3)],
            ),
            DataType.TIMESTAMP,
            kind=arg.kind,
        )

    def cast_date_to_timestamptz(
        self, arg: TypedSelectExpression, tz: str
    ) -> TypedSelectExpression:
        return TypedSelectExpression.from_sqlglot(
            exp.Anonymous(
                this="toDateTime64",
                expressions=[
                    arg.expression,
                    exp.Literal.number(3),
                    exp.Literal.string(tz),
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
        ClickHouse-specific day of week implementation using mode parameter.

        ClickHouse's toDayOfWeek with mode 3 returns Sunday=1, Saturday=7
        which matches our expected format.
        """

        if arg.data_type == DataType.TIMESTAMPTZ:
            arg = self.at_timezone(arg, timezone)

        # ClickHouse toDayOfWeek with mode 3: Sunday=1, Saturday=7
        dow_expr = self.func("toDayOfWeek", arg.expression, exp.Literal.number(3))

        return TypedSelectExpression.from_sqlglot(dow_expr, DataType.NUMBER, arg.kind)

    def contains(
        self, string: TypedSelectExpression, substring: TypedSelectExpression
    ) -> TypedSelectExpression:
        """
        Build expression to check if a string contains a substring using position.
        """

        kind = ExpressionKind._validate_infer_kind([string.kind, substring.kind])

        # Use position(string, substring) != 0
        pos_expr = self.func("position", string.expression, substring.expression)
        contains_expr = exp.NEQ(this=pos_expr, expression=exp.Literal.number(0))

        return TypedSelectExpression.from_sqlglot(contains_expr, DataType.BOOLEAN, kind)

    def startswith(
        self, string: TypedSelectExpression, prefix: TypedSelectExpression
    ) -> TypedSelectExpression:
        """
        Build expression to check if a string starts with a substring using
        ClickHouse's startsWith.
        """

        kind = ExpressionKind._validate_infer_kind([string.kind, prefix.kind])

        # ClickHouse has a native startsWith function
        startswith_expr = self.func("startsWith", string.expression, prefix.expression)

        return TypedSelectExpression.from_sqlglot(
            startswith_expr, DataType.BOOLEAN, kind
        )

    def endswith(
        self, string: TypedSelectExpression, suffix: TypedSelectExpression
    ) -> TypedSelectExpression:
        """
        Build expression to check if a string ends with a substring using
        ClickHouse's endsWith.
        """

        kind = ExpressionKind._validate_infer_kind([string.kind, suffix.kind])

        # ClickHouse has a native endsWith function
        endswith_expr = self.func("endsWith", string.expression, suffix.expression)

        return TypedSelectExpression.from_sqlglot(endswith_expr, DataType.BOOLEAN, kind)

    def concat(self, *args: TypedSelectExpression) -> TypedSelectExpression:
        """
        Build a CONCAT expression that treats NULLs as empty strings for ClickHouse.

        ClickHouse's concat returns NULL if any argument is NULL, so we need to wrap
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

    def cast_timestamp_to_string(
        self, arg: TypedSelectExpression
    ) -> TypedSelectExpression:
        """
        Cast a timestamp to string for ClickHouse.

        ClickHouse uses toDateTime() to remove fractional seconds before casting.
        This ensures timestamp-to-string conversion doesn't include fractional seconds.
        """

        # Use toDateTime() to remove fractional seconds, then cast to String
        datetime_expr = self.func("toDateTime", arg.expression)
        cast_expr = exp.Cast(this=datetime_expr, to=exp.DataType.build("String"))

        return TypedSelectExpression.from_sqlglot(
            cast_expr,
            DataType.STRING,
            arg.kind,
        )

    def splitpart(
        self,
        string: TypedSelectExpression,
        delimiter: TypedSelectExpression,
        part_number: TypedSelectExpression,
    ) -> TypedSelectExpression:
        """
        Clickhouse, ever the black sheep, has different function names and
        only supports constant delimiters in their splitByString function.
        To work around this, we first replace the delimiter in the string with
        a placeholder value, and then split the string on that. We then
        normalize edge cases with nulls and out of bounds indexes.
        """

        kind = ExpressionKind._validate_infer_kind(
            [
                string.kind,
                delimiter.kind,
                part_number.kind,
            ]
        )
        placeholder_str = self.compile_literal(
            "___hex_sl_clickhouse_delimiter_substitution___"
        ).expression
        split_array = exp.Anonymous(
            this="splitByString",
            expressions=[
                placeholder_str,
                exp.Anonymous(
                    this="replaceAll",
                    expressions=[
                        exp.Coalesce(
                            this=string.expression,
                            expressions=[self.compile_literal("").expression],
                        ),
                        delimiter.expression,
                        placeholder_str,
                    ],
                ),
            ],
        )

        return TypedSelectExpression.from_sqlglot(
            exp.Case()
            .when(exp.Is(this=string.expression, expression=exp.Null()), exp.Null())
            .when(
                exp.GT(
                    this=part_number.expression,
                    expression=exp.ArraySize(this=split_array),
                ),
                self.compile_literal("").expression,
            )
            .else_(
                exp.Bracket(
                    this=split_array,
                    expressions=[part_number.expression],
                )
            ),
            DataType.STRING,
            kind,
        )


class ClickHouseSqlGlotOverride(SqlGlotClickHouse):
    @classmethod
    def dialect_name(cls) -> str:
        return "hex-sl-clickhouse"

    # Clickhouse is always case sensitive, quoted or not
    NORMALIZATION_STRATEGY = NormalizationStrategy.CASE_SENSITIVE

    # From ibis
    TRANSFORMS = SqlGlotClickHouse.Generator.TRANSFORMS.copy() | {
        exp.ArraySize: rename_func("length"),
        exp.ArraySort: rename_func("arraySort"),
        exp.LogicalAnd: rename_func("min"),
        exp.LogicalOr: rename_func("max"),
    }

    class Generator(PlaceholderGeneratorMixin, SqlGlotClickHouse.Generator):
        def placeholder_sql(self, expression: exp.Placeholder) -> str:
            return placeholder_sql(self, expression)

        def values_sql(
            self, expression: exp.Values, values_as_table: bool = True
        ) -> str:
            # clickhouse doesn't support VALUES syntax
            return super().values_sql(expression, values_as_table=False)

        def variancepop_sql(self, expression: exp.VariancePop) -> str:
            """
            Override VariancePop to use ClickHouse's varPop function.
            """
            return f"varPop({self.sql(expression.this)})"

    class Tokenizer(SqlGlotClickHouse.Tokenizer):
        # Remove $ from heredoc strings to allow ${...} placeholders
        HEREDOC_STRINGS: ClassVar[list[str | tuple[str, str]]] = []

        # Add $ as PARAMETER token so ${...} can be parsed as placeholders
        SINGLE_TOKENS: ClassVar[dict[str, TokenType]] = {
            **tokens.Tokenizer.SINGLE_TOKENS,
            "$": TokenType.PARAMETER,
        }

    class Parser(SqlGlotClickHouse.Parser):
        PLACEHOLDER_PARSERS = placeholder_parser_mapping(
            SqlGlotClickHouse.Parser.PLACEHOLDER_PARSERS
        )

        def _parse_placeholder(self) -> exp.Expression | None:
            return parse_jinja_placeholder(self)
