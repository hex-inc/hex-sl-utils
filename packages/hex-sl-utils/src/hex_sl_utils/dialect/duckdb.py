from __future__ import annotations

import datetime
from typing import Any, Literal

from hex_sl_utils._vendor.sqlglot import exp, generator
from hex_sl_utils._vendor.sqlglot.dialects.duckdb import DuckDB as SqlGlotDuckDB
from hex_sl_utils._vendor.sqlglot.tokens import TokenType
from hex_sl_utils.datatype import DataType
from hex_sl_utils.dialect.dialect import Dialect
from hex_sl_utils.dialect.dialect_name import DialectName
from hex_sl_utils.expr import ExpressionContext, ExpressionKind, TypedSelectExpression
from hex_sl_utils.placeholder import (
    PlaceholderGeneratorMixin,
    parse_jinja_placeholder,
    placeholder_parser_mapping,
    placeholder_sql,
)
from hex_sl_utils.time import TimeTruncUnit


class DuckDB(Dialect):
    @classmethod
    def name(cls) -> DialectName:
        return "duckdb"

    @classmethod
    def sqlglot_dialect(cls) -> str:
        return "hex-sl-duckdb"

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

    def build_percentile_exact(
        self,
        arg: TypedSelectExpression,
        percentile: float,
    ) -> TypedSelectExpression:
        cast_typed = self.cast_to_float(arg)
        percentile_expr = self.func(
            "QUANTILE", cast_typed.expression, exp.Literal.number(percentile)
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
            "APPROX_QUANTILE", cast_typed.expression, exp.Literal.number(percentile)
        )

        return TypedSelectExpression.from_sqlglot(
            percentile_expr, DataType.NUMBER, arg.kind
        )

    def supports_non_finite_floats(self) -> bool:
        return True

    def build_isnan(self, arg: TypedSelectExpression) -> TypedSelectExpression:
        """
        Build an IS NAN check using DuckDB's native ISNAN function.
        """

        # Only cast if not already a float type
        if arg.data_type == DataType.NUMBER:
            # Already a float/double, use directly
            isnan_expr = self.func("ISNAN", arg.expression)
        else:
            # Cast to float first
            cast_arg = self.cast_to_float(arg)
            isnan_expr = self.func("ISNAN", cast_arg.expression)

        return TypedSelectExpression.from_sqlglot(
            isnan_expr, DataType.BOOLEAN, arg.kind
        )

    def build_isinf(self, arg: TypedSelectExpression) -> TypedSelectExpression:
        """
        Build an IS INFINITE check using DuckDB's native ISINF function.
        """

        # Only cast if not already a float type
        if arg.data_type == DataType.NUMBER:
            # Already a float/double, use directly
            isinf_expr = self.func("ISINF", arg.expression)
        else:
            # Cast to float first
            cast_arg = self.cast_to_float(arg)
            isinf_expr = self.func("ISINF", cast_arg.expression)

        return TypedSelectExpression.from_sqlglot(
            isinf_expr, DataType.BOOLEAN, arg.kind
        )

    def concat(self, *args: TypedSelectExpression) -> TypedSelectExpression:
        """
        Build a CONCAT expression for DuckDB.

        DuckDB's CONCAT function automatically skips NULL values in multi-argument
        calls and converts single NULL arguments to empty strings.
        """

        if len(args) == 0:
            return self.compile_literal("")
        else:
            kind = ExpressionKind._validate_infer_kind([arg.kind for arg in args])
            concat_expr = exp.Concat(expressions=[arg.expression for arg in args])
            return TypedSelectExpression.from_sqlglot(
                concat_expr, DataType.STRING, kind
            )

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
        Implements week truncation for DuckDB, always truncating to Sunday.

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
        Implements general date truncation for DuckDB

        Uses DuckDB's DATE_TRUNC function and handles timezone conversions
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
        # In DuckDB, the `AT TIME ZONE` clause returns a timestamp without timezone
        # (unlike Athena and BigQuery, which returns a timestamp with timezone).
        return TypedSelectExpression.from_sqlglot(
            exp.AtTimeZone(this=arg.expression, zone=exp.Literal.string(tz)),
            DataType.TIMESTAMP
            if arg.data_type == DataType.TIMESTAMPTZ
            else DataType.TIMESTAMPTZ,
            kind=arg.kind,
        )

    def epoch_ms_to_timestamp(
        self,
        arg: TypedSelectExpression,
    ) -> TypedSelectExpression:
        """
        Build expression to convert epoch milliseconds to a timestamp.

        DuckDB uses the epoch_ms() function for this conversion.
        """

        # Cast to int first if needed
        int_expr = exp.Cast(this=arg.expression, to=exp.DataType.build("BIGINT"))

        # Convert milliseconds to timestamp using epoch_ms
        timestamp_expr = self.func("epoch_ms", int_expr)

        naive_ts = TypedSelectExpression.from_sqlglot(
            timestamp_expr, DataType.TIMESTAMP, arg.kind
        )
        return self.at_timezone(naive_ts, "UTC")

    def datetime_to_epoch_ms(self, arg: TypedSelectExpression) -> TypedSelectExpression:
        """
        Build expression to convert a timestamp to epoch milliseconds.

        DuckDB uses the epoch_ms() function for this conversion.
        """

        if arg.data_type == DataType.TIMESTAMPTZ:
            # Always convert to UTC before extracting epoch millis
            arg = self.at_timezone(arg, "UTC")

        # Use DuckDB's epoch_ms function
        epoch_ms = self.func("epoch_ms", arg.expression)

        # Cast to BIGINT to get exact integers instead of floats
        casted = exp.Cast(this=epoch_ms, to=exp.DataType.build("BIGINT"))

        return TypedSelectExpression.from_sqlglot(casted, DataType.NUMBER, arg.kind)

    def cast_str_to_timestamp(
        self, arg: TypedSelectExpression, tz: str, force_tz: bool = False
    ) -> TypedSelectExpression:
        formats = [
            # ISO 8601 with and without time and 'T' separator
            "%Y-%m",
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%g",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%g",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d %H:%M",
            # With timezone offset
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S.%g%z",
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%dT%H:%M%z",
            "%Y-%m-%d %H:%M:%S%z",
            "%Y-%m-%d %H:%M:%S.%g%z",
            "%Y-%m-%d %H:%M:%S.%f%z",
            "%Y-%m-%d %H:%M%z",
            # ISO 8601 with forward slashes
            "%m/%d/%Y",
            "%m/%d/%Y %H:%M:%S",
            "%m/%d/%Y %H:%M:%S.%g",
            "%m/%d/%Y %H:%M:%S.%f",
            "%m/%d/%Y %H:%M",
            # e.g. May 1 2003
            "%b %-d %Y",
            "%b %-d %Y %H:%M:%S",
            "%b %-d %Y %H:%M:%S.%g",
            "%b %-d %Y %H:%M:%S.%f",
            "%b %-d %Y %H:%M",
            # ctime format (e.g. Sun Jul 8 00:34:60 2001)
            "%a %b %-d %H:%M:%S %Y",
            "%a %b %-d %H:%M:%S.%g %Y",
            "%a %b %-d %H:%M:%S.%f %Y",
            "%a %b %-d %H:%M %Y",
            # e.g. 01 Jan 2012 00:00:00
            "%d %b %Y",
            "%d %b %Y %H:%M:%S",
            "%d %b %Y %H:%M:%S.%g",
            "%d %b %Y %H:%M:%S.%f",
            "%d %b %Y %H:%M",
            # e.g. Sun, 01 Jan 2012 00:00:00
            "%a, %d %b %Y",
            "%a, %d %b %Y %H:%M:%S",
            "%a, %d %b %Y %H:%M:%S.%g",
            "%a, %d %b %Y %H:%M:%S.%f",
            "%a, %d %b %Y %H:%M",
            # e.g. December 17, 1995 03:00:00
            "%B %d, %Y",
            "%B %d, %Y %H:%M:%S",
            "%B %d, %Y %H:%M:%S.%g",
            "%B %d, %Y %H:%M:%S.%f",
            "%B %d, %Y %H:%M",
            # Workaround for https://github.com/duckdb/duckdb/issues/19016
            # More context in CUR-676
            "%Y-%m-%dT%H:%M:%S%Z",
        ]

        try_strptime_expr = exp.Anonymous(
            this="try_strptime",
            expressions=[arg.expression]
            + [exp.Array(expressions=[exp.Literal.string(fmt) for fmt in formats])],
        )

        # Cast to convert back to naive timestamp
        try_cast_expr = TypedSelectExpression.from_sqlglot(
            expression=exp.TryCast(
                this=try_strptime_expr, to=exp.DataType.build("TIMESTAMP")
            ),
            data_type=DataType.TIMESTAMP,
        )

        if force_tz:
            return self.at_timezone(try_cast_expr, tz)
        else:
            return try_cast_expr

    def should_cast_dimension_type_by_default(self, dtype: DataType) -> bool:
        # In duckdb it's safe to always cast to timestamptz, and
        # this handles the scenario where the true column type is timestamp.
        return dtype == DataType.TIMESTAMPTZ

    def compile_literal(
        self,
        literal: Any,
        context: ExpressionContext | None = None,
        data_type: DataType | None = None,
    ) -> TypedSelectExpression:
        """
        Compile a literal expression with DuckDB-specific date handling.

        DuckDB uses MAKE_DATE for date literals.
        """

        # Handle datetime objects with DuckDB-specific MAKE_TIMESTAMP function
        if isinstance(literal, datetime.datetime):
            # Check if datetime has timezone info
            if literal.tzinfo is not None:
                # This is a timezone-aware datetime (TIMESTAMPTZ)
                # Use MAKE_TIMESTAMPTZ with timezone string
                # Extract microseconds
                microseconds = literal.microsecond

                # Get timezone string from tzinfo
                tz_str = str(literal.tzinfo)
                if tz_str.startswith("datetime.timezone.utc"):
                    tz_str = "UTC"

                ts_expr = self.func(
                    "MAKE_TIMESTAMPTZ",
                    exp.Literal.number(literal.year),
                    exp.Literal.number(literal.month),
                    exp.Literal.number(literal.day),
                    exp.Literal.number(literal.hour),
                    exp.Literal.number(literal.minute),
                    exp.Literal.number(literal.second + microseconds / 1000000.0),
                    exp.Literal.string(tz_str),
                )
                result = TypedSelectExpression.from_sqlglot(
                    ts_expr, DataType.TIMESTAMPTZ, ExpressionKind.SCALAR
                )
            else:
                # This is a naive datetime (TIMESTAMP)
                # Use MAKE_TIMESTAMP
                # Extract microseconds
                microseconds = literal.microsecond
                ts_expr = self.func(
                    "MAKE_TIMESTAMP",
                    exp.Literal.number(literal.year),
                    exp.Literal.number(literal.month),
                    exp.Literal.number(literal.day),
                    exp.Literal.number(literal.hour),
                    exp.Literal.number(literal.minute),
                    exp.Literal.number(literal.second + microseconds / 1000000.0),
                )
                result = TypedSelectExpression.from_sqlglot(
                    ts_expr, DataType.TIMESTAMP, ExpressionKind.SCALAR
                )
            if context is not None:
                result = self.wrap_expression_for_context(result, context)
            return result
        # Handle date objects with DuckDB-specific MAKE_DATE function
        elif isinstance(literal, datetime.date) and not isinstance(
            literal, datetime.datetime
        ):
            # Use MAKE_DATE(year, month, day) for DuckDB
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
            # DuckDB uses 'ms' with quotes for milliseconds
            extract_base = exp.Extract(
                this=exp.Literal.string("ms"), expression=arg.expression
            )
            extract_expr = exp.Mod(
                this=extract_base, expression=exp.Literal.number(1000)
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

    def startswith(
        self, string: TypedSelectExpression, prefix: TypedSelectExpression
    ) -> TypedSelectExpression:
        """
        DuckDB-specific startswith implementation using native STARTS_WITH function.
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
        DuckDB-specific endswith implementation using native SUFFIX function.
        """

        kind = ExpressionKind._validate_infer_kind([string.kind, suffix.kind])
        # DuckDB uses SUFFIX function for endswith
        endswith_expr = self.func("SUFFIX", string.expression, suffix.expression)
        return TypedSelectExpression.from_sqlglot(endswith_expr, DataType.BOOLEAN, kind)

    def contains(
        self, string: TypedSelectExpression, substring: TypedSelectExpression
    ) -> TypedSelectExpression:
        """
        Build expression to check if a string contains a substring using CONTAINS.
        """

        kind = ExpressionKind._validate_infer_kind([string.kind, substring.kind])

        # DuckDB has a native CONTAINS function
        contains_expr = self.func("CONTAINS", string.expression, substring.expression)

        return TypedSelectExpression.from_sqlglot(contains_expr, DataType.BOOLEAN, kind)

    def splitpart(
        self,
        string: TypedSelectExpression,
        delimiter: TypedSelectExpression,
        part_number: TypedSelectExpression,
    ) -> TypedSelectExpression:
        """
        Build expression to split a string and extract the specified part.

        Uses DuckDB's native SPLIT_PART function which returns empty string for
        out-of-bounds indices and handles null strings by returning null.
        """

        kind = ExpressionKind._validate_infer_kind(
            [string.kind, delimiter.kind, part_number.kind]
        )

        # Use DuckDB's native SPLIT_PART function
        split_part_expr = self.func(
            "SPLIT_PART",
            string.expression,
            delimiter.expression,
            part_number.expression,
        )

        return TypedSelectExpression.from_sqlglot(
            split_part_expr, DataType.STRING, kind
        )


class DuckDBSqlGlotOverride(SqlGlotDuckDB):
    @classmethod
    def dialect_name(cls) -> str:
        return "hex-sl-duckdb"

    class Generator(PlaceholderGeneratorMixin, SqlGlotDuckDB.Generator):
        def placeholder_sql(self, expression: exp.Placeholder) -> str:
            return placeholder_sql(self, expression)

        def interval_sql(self, expression: exp.Interval) -> str:
            # sqlglot tries to convert intervals to days, which duckdb doesn't need,
            # And it messes up months and quarters.
            return generator.Generator.interval_sql(self, expression)

    class Parser(SqlGlotDuckDB.Parser):
        NO_PAREN_FUNCTION_PARSERS = (
            SqlGlotDuckDB.Parser.NO_PAREN_FUNCTION_PARSERS.copy()
        )
        NO_PAREN_FUNCTION_PARSERS.pop("@", None)

        PLACEHOLDER_PARSERS = placeholder_parser_mapping(
            SqlGlotDuckDB.Parser.PLACEHOLDER_PARSERS,
            parameter_fallback=lambda self: (
                self.expression(exp.Placeholder, this=getattr(self._prev, "text", ""))
                if self._match(TokenType.NUMBER) or self._match_set(self.ID_VAR_TOKENS)
                else None
            ),
        )

        def _parse_placeholder(self) -> exp.Expression | None:
            return parse_jinja_placeholder(self)
