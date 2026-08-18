from __future__ import annotations

import datetime
from typing import Any

from hex_sl_utils._vendor.sqlglot import exp, transforms
from hex_sl_utils._vendor.sqlglot.dialects.spark import Spark as SqlGlotSpark
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
from hex_sl_utils.dialect.transforms import hex_sl_eliminate_qualify
from hex_sl_utils.expr import ExpressionContext, ExpressionKind, TypedSelectExpression
from hex_sl_utils.time import TimeTruncUnit


class Spark(Dialect):
    @classmethod
    def name(cls) -> DialectName:
        return "spark"

    @classmethod
    def sqlglot_dialect(cls) -> str:
        return "hex-sl-spark"

    def supports_window_partition_by_alias(self) -> bool:
        return False

    def truncates_on_integer_division(self) -> bool:
        return False

    def mod_supports_floats(self) -> bool:
        return True

    def supports_median(self) -> bool:
        return True

    def supports_percentile_exact(self) -> bool:
        return True

    def supports_percentile_approx(self) -> bool:
        return True

    def supports_non_finite_floats(self) -> bool:
        return True

    def build_isnan(self, arg: TypedSelectExpression) -> TypedSelectExpression:
        """
        Build an IS NAN check using Spark's native ISNAN function.
        """

        # Use Spark's native ISNAN function
        cast_arg = self.cast_to_float(arg)
        isnan_expr = self.func("ISNAN", cast_arg.expression)

        return TypedSelectExpression.from_sqlglot(
            isnan_expr, DataType.BOOLEAN, arg.kind
        )

    def build_median(self, arg: TypedSelectExpression) -> TypedSelectExpression:
        """
        Build a MEDIAN expression for Spark.

        Spark uses PERCENTILE(cast_arg, 0.5) for median calculation.
        """

        # Cast to DOUBLE using dialect method
        cast_typed = self.cast_to_float(arg)

        # Use PERCENTILE function with 0.5 (not PERCENTILE_APPROX)
        median_expr = self.func(
            "PERCENTILE", cast_typed.expression, exp.Literal.number(0.5)
        )

        return TypedSelectExpression.from_sqlglot(
            median_expr, DataType.NUMBER, arg.kind
        )

    def build_percentile_exact(
        self,
        arg: TypedSelectExpression,
        percentile: float,
    ) -> TypedSelectExpression:
        cast_typed = self.cast_to_float(arg)
        percentile_expr = self.func(
            "PERCENTILE", cast_typed.expression, exp.Literal.number(percentile)
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
        percentile_expr = self.func(
            "percentile_approx", cast_typed.expression, exp.Literal.number(percentile)
        )

        return TypedSelectExpression.from_sqlglot(
            percentile_expr, DataType.NUMBER, arg.kind
        )

    def compile_literal(
        self,
        literal: Any,
        context: ExpressionContext | None = None,
        data_type: DataType | None = None,
    ) -> TypedSelectExpression:
        """
        Compile a literal expression with Spark-specific date and datetime handling.

        Spark uses MAKE_DATE(year, month, day) for date literals and
        CAST('string' AS TIMESTAMP) for datetime literals.
        """

        # Handle datetime objects with Spark-specific CAST functions
        if isinstance(literal, datetime.datetime):
            # Both timezone-aware and naive datetimes use CAST with 'T' separator
            # in Spark
            # Use isoformat() to get 'T' separator (override base implementation)
            dt_str = literal.isoformat()
            ts_expr = exp.Cast(
                this=exp.Literal.string(dt_str), to=exp.DataType.build("TIMESTAMP")
            )
            # Spark treats both as TIMESTAMP type
            result = TypedSelectExpression.from_sqlglot(
                ts_expr, DataType.TIMESTAMP, ExpressionKind.SCALAR
            )
            if context is not None:
                result = self.wrap_expression_for_context(result, context)
            return result

        # Handle date objects with Spark-specific MAKE_DATE function
        elif isinstance(literal, datetime.date) and not isinstance(
            literal, datetime.datetime
        ):
            # Use MAKE_DATE(year, month, day) for Spark
            date_expr = self.func(
                "MAKE_DATE",
                exp.Literal.number(literal.year),
                exp.Literal.number(literal.month),
                exp.Literal.number(literal.day),
            )
            result = TypedSelectExpression.from_sqlglot(
                date_expr, DataType.DATE, ExpressionKind.SCALAR
            )
            if context is not None:
                result = self.wrap_expression_for_context(result, context)
            return result

        # For all other types, use the base implementation
        return super().compile_literal(literal, context, data_type)

    def epoch_ms_to_timestamp(
        self, arg: TypedSelectExpression
    ) -> TypedSelectExpression:
        """
        Build expression to convert epoch milliseconds to a timestamp.
        """

        # Convert epoch milliseconds to timestamp
        ts_from_seconds = self.func(
            "to_utc_timestamp",
            self.func(
                "from_unixtime",
                exp.Div(
                    this=exp.paren(arg.expression),
                    expression=exp.Literal.number(1000),
                ),
            ),
            self.func("current_timezone"),
        )

        # Add milliseconds to the result
        ts = self.func(
            "date_add",
            exp.Literal(this="millisecond", is_string=False),
            exp.Mod(
                this=exp.paren(arg.expression), expression=exp.Literal.number(1000)
            ),
            ts_from_seconds,
        )

        return TypedSelectExpression.from_sqlglot(
            ts,
            DataType.TIMESTAMPTZ,
            kind=arg.kind,
        )

    def datetime_to_epoch_ms(self, arg: TypedSelectExpression) -> TypedSelectExpression:
        """
        Build expression to convert a timestamp to epoch milliseconds.
        """

        epoch_seconds: exp.Expression
        if arg.data_type == DataType.TIMESTAMPTZ:
            # Already in UTC
            epoch_seconds = self.func("unix_timestamp", arg.expression)
        else:
            # Convert to local timestamp first
            epoch_seconds = self.func(
                "unix_timestamp",
                self.func(
                    "from_utc_timestamp",
                    arg.expression,
                    self.func("current_timezone"),
                ),
            )

        # Extract milliseconds from the timestamp
        millis = exp.cast(
            exp.Mul(
                this=exp.Mod(
                    this=exp.Extract(
                        this=exp.Literal.string("seconds"),
                        expression=arg.expression,
                    ),
                    expression=exp.Literal.number(1),
                ),
                expression=exp.Literal.number(1000),
            ),
            to=exp.DataType.Type.BIGINT,
        )

        # Add milliseconds to the result
        epoch_millis_add = exp.Add(
            this=exp.Mul(this=epoch_seconds, expression=exp.Literal.number(1000)),
            expression=millis,
        )

        # Wrap the entire expression in parentheses to ensure proper precedence in
        # arithmetic operations
        epoch_millis = exp.Paren(this=epoch_millis_add)

        return TypedSelectExpression.from_sqlglot(
            epoch_millis,
            DataType.NUMBER,
            kind=arg.kind,
        )

    def datetime_trunc(
        self,
        arg: TypedSelectExpression,
        unit: TimeTruncUnit,
        tz: str,
    ) -> TypedSelectExpression:
        convert_tz = tz if arg.data_type == DataType.TIMESTAMPTZ else None

        # Apply timezone if provided, otherwise use the original expression
        tz_expression = (
            self.func(
                "from_utc_timestamp",
                arg.expression,
                exp.Literal.string(convert_tz),
            )
            if convert_tz is not None
            else arg.expression
        )

        date_trunc_expr: exp.Expression
        if unit == "week":
            date_trunc_expr = self.func(
                "DATE_ADD",
                exp.TimestampTrunc(  # type: ignore[no-untyped-call]
                    unit=exp.Literal.string("week"),
                    this=self.func("DATE_ADD", tz_expression, exp.Literal.number(1)),
                ),
                exp.Literal.number(-1),
            )
        else:
            sql_unit = "week" if unit == "weekmonday" else unit
            # Build the DATE_TRUNC function call
            date_trunc_expr = exp.TimestampTrunc(  # type: ignore[no-untyped-call]
                unit=exp.Literal.string(sql_unit), this=tz_expression
            )

        if arg.data_type == DataType.DATE:
            date_trunc_expr = exp.Cast(
                this=date_trunc_expr, to=exp.DataType.build("DATE")
            )
        elif unit in self._DATE_UNITS:
            # make sure to return a timestamp if the input is not a date,
            # but truncation was a date unit
            date_trunc_expr = exp.Cast(
                this=date_trunc_expr, to=exp.DataType.build("TIMESTAMP")
            )

        # Re-apply timezone if provided
        if convert_tz is not None:
            date_trunc_expr = self.func(
                "to_utc_timestamp",
                date_trunc_expr,
                exp.Literal.string(convert_tz),
            )

        return TypedSelectExpression.from_sqlglot(
            date_trunc_expr,
            arg.data_type,
            kind=arg.kind,
        )

    def day_of_week_part(
        self,
        arg: TypedSelectExpression,
        timezone: str,
    ) -> TypedSelectExpression:
        """
        Spark-specific day of week implementation.

        Spark uses DAYOFWEEK(TO_DATE(date)) which returns Sunday=1, Saturday=7.
        This already matches our expected format, so no adjustment needed.
        """

        if arg.data_type == DataType.TIMESTAMPTZ:
            arg = self.at_timezone(arg, timezone)

        # Spark DAYOFWEEK(TO_DATE(date)) returns Sunday=1, Saturday=7 which is
        # what we want
        dow_expr = self.func("DAYOFWEEK", self.func("TO_DATE", arg.expression))

        return TypedSelectExpression.from_sqlglot(dow_expr, DataType.NUMBER, arg.kind)

    def at_timezone(self, arg: TypedSelectExpression, tz: str) -> TypedSelectExpression:
        if arg.data_type == DataType.TIMESTAMPTZ:
            return TypedSelectExpression.from_sqlglot(
                exp.cast(
                    self.func(
                        "convert_timezone",
                        exp.Literal.string("UTC"),
                        exp.Literal.string(tz),
                        arg.expression,
                    ),
                    to=exp.DataType.build("TIMESTAMP"),
                ),
                DataType.TIMESTAMP,
                kind=arg.kind,
            )
        else:
            return TypedSelectExpression.from_sqlglot(
                exp.cast(
                    self.func(
                        "convert_timezone",
                        exp.Literal.string(tz),
                        exp.Literal.string("UTC"),
                        arg.expression,
                    ),
                    to=exp.DataType.build("TIMESTAMP"),
                ),
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

        # Use EXTRACT function
        extract_expr: exp.Expression
        if unit == "millisecond":
            # Use DATE_FORMAT with 'SSS' pattern for milliseconds
            extract_expr = exp.Cast(
                this=self.func(
                    "DATE_FORMAT", arg.expression, exp.Literal.string("SSS")
                ),
                to=exp.DataType.build("INT"),
            )
        else:
            extract_expr = exp.Extract(
                this=exp.Literal.string(unit.upper()), expression=arg.expression
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
        Spark-specific startswith implementation using native STARTSWITH function.
        """

        kind = ExpressionKind._validate_infer_kind([string.kind, prefix.kind])
        startswith_expr = self.func("STARTSWITH", string.expression, prefix.expression)
        return TypedSelectExpression.from_sqlglot(
            startswith_expr, DataType.BOOLEAN, kind
        )

    def endswith(
        self, string: TypedSelectExpression, suffix: TypedSelectExpression
    ) -> TypedSelectExpression:
        """
        Spark-specific endswith implementation using native ENDSWITH function.
        """

        kind = ExpressionKind._validate_infer_kind([string.kind, suffix.kind])
        endswith_expr = self.func("ENDSWITH", string.expression, suffix.expression)
        return TypedSelectExpression.from_sqlglot(endswith_expr, DataType.BOOLEAN, kind)

    def concat(self, *args: TypedSelectExpression) -> TypedSelectExpression:
        """
        Build a CONCAT expression that treats NULLs as empty strings for Spark.

        Spark's CONCAT returns NULL if any argument is NULL, so we need to wrap
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

    def contains(
        self, string: TypedSelectExpression, substring: TypedSelectExpression
    ) -> TypedSelectExpression:
        """
        Build expression to check if a string contains a substring using CONTAINS.
        """

        kind = ExpressionKind._validate_infer_kind([string.kind, substring.kind])

        # Spark has a native CONTAINS function
        contains_expr = self.func("CONTAINS", string.expression, substring.expression)

        return TypedSelectExpression.from_sqlglot(contains_expr, DataType.BOOLEAN, kind)


class SparkSqlGlotOverride(SqlGlotSpark):
    @classmethod
    def dialect_name(cls) -> str:
        return "hex-sl-spark"

    class Generator(PlaceholderGeneratorMixin, SqlGlotSpark.Generator):
        TRANSFORMS = SqlGlotSpark.Generator.TRANSFORMS.copy() | {
            exp.Select: transforms.preprocess(
                [
                    transforms.eliminate_semi_and_anti_joins,
                    hex_sl_eliminate_qualify,
                ]
            ),
        }

        def placeholder_sql(self, expression: exp.Placeholder) -> str:
            return placeholder_sql(self, expression)

    class Parser(SqlGlotSpark.Parser):
        PLACEHOLDER_PARSERS = placeholder_parser_mapping(
            SqlGlotSpark.Parser.PLACEHOLDER_PARSERS,
            parameter_fallback=lambda self: (
                self.expression(exp.Placeholder, this=getattr(self._prev, "text", ""))
                if self._match(TokenType.NUMBER) or self._match_set(self.ID_VAR_TOKENS)
                else None
            ),
        )

        def _parse_placeholder(self) -> exp.Expression | None:
            return parse_jinja_placeholder(self)
