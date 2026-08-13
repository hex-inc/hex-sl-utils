from __future__ import annotations

import datetime
from typing import Any, Literal

from hex_sl_utils._vendor.sqlglot import exp, transforms
from hex_sl_utils._vendor.sqlglot.dialects.dialect import rename_func
from hex_sl_utils._vendor.sqlglot.dialects.postgres import Postgres
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


class HexSLPostgres(HexSLDialect):
    @classmethod
    def name(cls) -> DialectName:
        return "postgres"

    @classmethod
    def sqlglot_dialect(cls) -> str:
        return "hex-sl-postgres"

    def supports_window_partition_by_alias(self) -> bool:
        return False

    def truncates_on_integer_division(self) -> bool:
        return True

    def mod_supports_floats(self) -> bool:
        return True

    def supports_median(self) -> bool:
        return True

    def supports_percentile_exact(self) -> bool:
        return True

    def supports_non_finite_floats(self) -> bool:
        return True

    def build_isnan(self, arg: TypedSelectExpression) -> TypedSelectExpression:
        """
        Build an IS NAN check using Postgres' comparison approach.

        PostgreSQL: NaN = NaN returns true, but NaN != NaN returns false.
        So we check: arg = 'NaN'::DOUBLE PRECISION
        """

        # Cast argument to double precision
        cast_arg = self.cast_to_float(arg)

        # Compare with NaN literal: arg = 'NaN'::DOUBLE PRECISION
        nan_literal = exp.Cast(
            this=exp.Literal.string("NaN"), to=exp.DataType.build("DOUBLE PRECISION")
        )
        isnan_expr = exp.EQ(this=cast_arg.expression, expression=nan_literal)

        return TypedSelectExpression.from_sqlglot(
            isnan_expr, DataType.BOOLEAN, arg.kind
        )

    def build_median(self, arg: TypedSelectExpression) -> TypedSelectExpression:
        """
        Build a MEDIAN expression using PERCENTILE_CONT for Postgres.
        """

        # Cast to float using dialect method
        cast_typed = self.cast_to_float(arg)

        # Use PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY expr)
        median_anon = exp.Anonymous(
            this="PERCENTILE_CONT", expressions=[exp.Literal.number(0.5)]
        )
        # Add WITHIN GROUP (ORDER BY expr) clause
        median_expr = exp.WithinGroup(
            this=median_anon,
            expression=exp.Order(expressions=[exp.Ordered(this=cast_typed.expression)]),
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
        percentile_anon = exp.Anonymous(
            this="PERCENTILE_CONT", expressions=[exp.Literal.number(percentile)]
        )
        percentile_expr = exp.WithinGroup(
            this=percentile_anon,
            expression=exp.Order(expressions=[exp.Ordered(this=cast_typed.expression)]),
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
        Compile a literal expression with Postgres-specific date and datetime handling.

        Postgres uses MAKE_DATE(year, month, day) for date literals and
        CAST('string' AS TIMESTAMP/TIMESTAMPTZ) for datetime literals.
        """

        # Handle datetime objects with Postgres-specific CAST functions
        if isinstance(literal, datetime.datetime):
            # Check if datetime has timezone info
            if literal.tzinfo is not None:
                # This is a timezone-aware datetime (TIMESTAMPTZ)
                # Use isoformat() to get 'T' separator and proper timezone format
                dt_str = literal.isoformat()
                ts_expr = exp.Cast(
                    this=exp.Literal.string(dt_str),
                    to=exp.DataType.build("TIMESTAMPTZ"),
                )
                result = TypedSelectExpression.from_sqlglot(
                    ts_expr, DataType.TIMESTAMPTZ, ExpressionKind.SCALAR
                )
            else:
                # This is a naive datetime (TIMESTAMP)
                # Use isoformat() to get 'T' separator (override base implementation)
                dt_str = literal.isoformat()
                ts_expr = exp.Cast(
                    this=exp.Literal.string(dt_str), to=exp.DataType.build("TIMESTAMP")
                )
                result = TypedSelectExpression.from_sqlglot(
                    ts_expr, DataType.TIMESTAMP, ExpressionKind.SCALAR
                )

            if context is not None:
                result = self.wrap_expression_for_context(result, context)
            return result

        # Handle date objects with Postgres-specific MAKE_DATE function
        elif isinstance(literal, datetime.date) and not isinstance(
            literal, datetime.datetime
        ):
            # Use MAKE_DATE(year, month, day) for Postgres
            make_date_expr = self.func(
                "MAKE_DATE",
                exp.Literal.number(literal.year),
                exp.Literal.number(literal.month),
                exp.Literal.number(literal.day),
            )
            result = TypedSelectExpression.from_sqlglot(
                make_date_expr, DataType.DATE, ExpressionKind.SCALAR
            )
            if context is not None:
                result = self.wrap_expression_for_context(result, context)
            return result

        # For all other types, use the base implementation
        return super().compile_literal(literal, context, data_type)

    def cast_str_to_date(self, arg: TypedSelectExpression) -> TypedSelectExpression:
        """
        Build expression to cast string to date, or null if the string is not a date
        """

        str_as_date = (
            exp.Case()
            .when(
                exp.RegexpLike(
                    this=arg.expression,
                    expression=exp.Literal.string(r"^\d{4}-\d{2}-\d{2}$"),
                ),
                exp.Cast(this=arg.expression, to=exp.DataType.build("DATE")),
            )
            .else_(exp.Null())
        )
        return TypedSelectExpression.from_sqlglot(
            str_as_date,
            DataType.DATE,
            arg.kind,
        )

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

    def epoch_ms_to_timestamp(
        self, arg: TypedSelectExpression
    ) -> TypedSelectExpression:
        """
        Build expression to convert epoch milliseconds to a timestamp.
        """

        # TO_TIMESTAMP(arg / 1000)
        return TypedSelectExpression.from_sqlglot(
            exp.Anonymous(
                this="TO_TIMESTAMP",
                expressions=[
                    exp.Div(
                        this=arg.expression,
                        expression=exp.Literal.number(1000),
                    ),
                ],
            ),
            DataType.TIMESTAMPTZ,
            kind=arg.kind,
        )

    def datetime_to_epoch_ms(self, arg: TypedSelectExpression) -> TypedSelectExpression:
        """
        Build expression to convert a timestamp to epoch milliseconds.

        Postgres uses EXTRACT('epoch' FROM ...) to get epoch seconds.
        """

        if arg.data_type == DataType.TIMESTAMPTZ:
            # Always convert to UTC before extracting epoch millis
            arg = self.at_timezone(arg, "UTC")

        # Use EXTRACT('epoch' FROM arg) to get epoch seconds, then multiply by
        # 1000 and floor
        epoch_seconds = exp.Extract(
            this=exp.Literal.string("epoch"), expression=arg.expression
        )

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
        if unit.lower() == "week":
            result_expr = self._trunc_week(arg.expression, convert_tz)
        else:
            sql_unit = "week" if unit.lower() == "weekmonday" else unit
            result_expr = self._trunc_general(arg.expression, sql_unit, convert_tz)

        if arg.data_type == DataType.DATE:
            result_expr = exp.Cast(this=result_expr, to=exp.DataType.build("DATE"))
        elif unit in self._DATE_UNITS and arg.data_type == DataType.TIMESTAMP:
            result_expr = exp.Cast(this=result_expr, to=exp.DataType.build("TIMESTAMP"))

        return TypedSelectExpression.from_sqlglot(
            result_expr,
            arg.data_type,
            kind=arg.kind,
        )

    def _trunc_week(
        self,
        expr: exp.Expression,
        convert_tz: str | None,
    ) -> exp.Expression:
        """
        Implements week truncation for Postgres, always truncating to Sunday.

        The generated SQL will look like this:
        (DATE_TRUNC('week', (expr + INTERVAL 1 day)) - INTERVAL 1 day)

        If a timezone is provided, it applies AT TIME ZONE before and after
        the truncation.

        Args:
            expr: The expression representing the date to be truncated.
            convert_tz: The timezone to be used for the truncation, if any.

        Returns:
            exp.Expression: A new expression representing the date truncated to the
                            start of the week (Sunday).
        """
        # Add 1 day
        adjusted_expr: exp.Expression = exp.Paren(
            this=exp.Add(
                this=expr,
                expression=exp.Interval(this=exp.Literal.number(1), unit="day"),  # type: ignore[no-untyped-call]
            )
        )

        # Apply timezone if provided
        if convert_tz is not None:
            adjusted_expr = exp.AtTimeZone(
                this=adjusted_expr, zone=exp.Literal.string(convert_tz)
            )

        # Truncate to week
        truncated_expr = self.func(
            "DATE_TRUNC", exp.Literal.string("week"), adjusted_expr
        )

        # Subtract 1 day
        result_expr: exp.Expression = exp.Sub(
            this=truncated_expr,
            expression=exp.Interval(this=exp.Literal.number(1), unit="day"),  # type: ignore[no-untyped-call]
        )

        # Re-apply timezone if provided
        if convert_tz is not None:
            result_expr = exp.AtTimeZone(
                this=exp.Paren(this=result_expr),
                zone=exp.Literal.string(convert_tz),
            )

        return result_expr

    def _trunc_general(
        self,
        expr: exp.Expression,
        unit: TimeTruncUnit,
        convert_tz: str | None,
    ) -> exp.Expression:
        """
        Implements general date truncation for Postgres

        Uses Postgres's DATE_TRUNC function and handles timezone conversions
        when provided.

        Args:
            expr: The expression representing the date/time to be truncated.
            unit: The unit to truncate to (e.g., 'year', 'month', 'day', 'hour', etc.).
            convert_tz: The timezone to be used for the truncation, if any.

        Returns:
            exp.Expression: A new expression representing the truncated date/time.
        """
        # Apply timezone if provided
        if convert_tz is not None:
            expr = exp.AtTimeZone(this=expr, zone=exp.Literal.string(convert_tz))

        # Truncate
        result_expr: exp.Expression = self.func(
            "DATE_TRUNC", exp.Literal.string(unit), expr
        )

        # Re-apply timezone if provided
        if convert_tz is not None:
            result_expr = exp.AtTimeZone(
                this=result_expr, zone=exp.Literal.string(convert_tz)
            )

        return result_expr

    def at_timezone(self, arg: TypedSelectExpression, tz: str) -> TypedSelectExpression:

        # In Postgres, the `AT TIME ZONE` clause returns a timestamp without timezone
        # (unlike Athena and BigQuery, which returns a timestamp with timezone).
        return TypedSelectExpression.from_sqlglot(
            exp.AtTimeZone(this=arg.expression, zone=exp.Literal.string(tz)),
            DataType.TIMESTAMP
            if arg.data_type == DataType.TIMESTAMPTZ
            else DataType.TIMESTAMPTZ,
            kind=arg.kind,
        )

    def time_part(
        self,
        arg: TypedSelectExpression,
        unit: Literal["hour", "minute", "second", "millisecond"],
        timezone: str,
    ) -> TypedSelectExpression:
        if unit == "millisecond" and arg.data_type != DataType.DATE:
            # ibis generates an expression like:
            #   CAST(FLOOR(EXTRACT('millisecond' FROM "ts")) % 1000 AS INT)
            #
            # But this is resulting in an error:
            #   "operator does not exist: double precision % integer"
            #
            # The cast to int needs to happen before the mod operation, like this:
            #   CAST(FLOOR(EXTRACT('millisecond' FROM "ts")) AS INT) % 1000

            return TypedSelectExpression.from_sqlglot(
                exp.Mod(
                    this=exp.Cast(
                        this=exp.Floor(
                            this=exp.Extract(
                                this=exp.Literal.string("millisecond"),
                                expression=arg.expression,
                            ),
                        ),
                        to=exp.DataType(this=exp.DataType.Type.INT, nested=False),
                    ),
                    expression=exp.Literal.number(1000),
                ),
                DataType.NUMBER,
                kind=arg.kind,
            )
        elif unit == "second" and arg.data_type != DataType.DATE:
            # Postgres EXTRACT returns fractional seconds, so we need to floor them
            # to match expected behavior (truncate, not round)

            if arg.data_type == DataType.TIMESTAMPTZ:
                arg = self.at_timezone(arg, timezone)

            # CAST(FLOOR(EXTRACT('second' FROM ts)) AS INT)
            extract_expr = exp.Extract(
                this=exp.Literal.string("second"), expression=arg.expression
            )
            floored_expr = exp.Floor(this=extract_expr)
            casted_expr = exp.Cast(this=floored_expr, to=exp.DataType.build("INT"))

            return TypedSelectExpression.from_sqlglot(
                casted_expr,
                DataType.NUMBER,
                kind=arg.kind,
            )
        else:
            return super().time_part(arg, unit, timezone)

    def splitpart(
        self,
        string: TypedSelectExpression,
        delimiter: TypedSelectExpression,
        part_number: TypedSelectExpression,
    ) -> TypedSelectExpression:
        """
        PostgreSQL-specific splitpart implementation using native SPLIT_PART function.

        Uses PostgreSQL's native SPLIT_PART function which returns empty string for
        out-of-bounds indices and handles null strings by returning null.
        """

        kind = ExpressionKind._validate_infer_kind(
            [string.kind, delimiter.kind, part_number.kind]
        )

        # Use PostgreSQL's native SPLIT_PART function
        split_part_expr = self.func(
            "SPLIT_PART",
            string.expression,
            delimiter.expression,
            part_number.expression,
        )

        return TypedSelectExpression.from_sqlglot(
            split_part_expr, DataType.STRING, kind
        )

    def concat(self, *args: TypedSelectExpression) -> TypedSelectExpression:
        """
        Build a CONCAT expression for PostgreSQL.

        PostgreSQL's CONCAT function handles NULLs perfectly in all cases:
        - Multi-argument calls automatically skip NULL values
        - Single NULL arguments are converted to empty strings
        No COALESCE wrapping is needed.
        """

        if len(args) == 0:
            return self.compile_literal("")
        else:
            kind = ExpressionKind._validate_infer_kind([arg.kind for arg in args])
            concat_expr = exp.Concat(expressions=[arg.expression for arg in args])
            return TypedSelectExpression.from_sqlglot(
                concat_expr, DataType.STRING, kind
            )

    def startswith(
        self, string: TypedSelectExpression, prefix: TypedSelectExpression
    ) -> TypedSelectExpression:
        """
        PostgreSQL-specific startswith implementation using native STARTS_WITH function.
        """

        kind = ExpressionKind._validate_infer_kind([string.kind, prefix.kind])
        startswith_expr = self.func("STARTS_WITH", string.expression, prefix.expression)
        return TypedSelectExpression.from_sqlglot(
            startswith_expr, DataType.BOOLEAN, kind
        )

    def should_cast_dimension_type_by_default(self, dtype: DataType) -> bool:
        # In postgres it's safe to always cast to timestamptz, and
        # this handles the scenario where the true column type is timestamp.
        return dtype == DataType.TIMESTAMPTZ


class HexSlPostgresSqlGlotDialect(Postgres):
    @classmethod
    def dialect_name(cls) -> str:
        return "hex-sl-postgres"

    class Generator(HexSLPlaceholderGeneratorMixin, Postgres.Generator):
        def placeholder_sql(self, expression: exp.Placeholder) -> str:
            return placeholder_sql(self, expression)

        # From ibis
        TRANSFORMS = Postgres.Generator.TRANSFORMS.copy() | {
            exp.Map: rename_func("hstore"),
            exp.Split: rename_func("string_to_array"),
            exp.RegexpSplit: rename_func("regexp_split_to_array"),
            exp.DateFromParts: rename_func("make_date"),
            exp.ArraySize: rename_func("cardinality"),
            exp.Pow: rename_func("pow"),
            exp.Select: transforms.preprocess(
                [
                    transforms.eliminate_semi_and_anti_joins,
                    hex_sl_eliminate_qualify,
                ]
            ),
        }

    class Parser(Postgres.Parser):
        PLACEHOLDER_PARSERS = placeholder_parser_mapping(
            Postgres.Parser.PLACEHOLDER_PARSERS,
            parameter_fallback=lambda self: (
                self.expression(
                    exp.Placeholder,
                    this=getattr(self._prev, "text", ""),
                    jdbc=True,
                )
                if self._match(TokenType.NUMBER)
                else None
            ),
        )

        def _parse_placeholder(self) -> exp.Expression | None:
            return parse_jinja_placeholder(self)
