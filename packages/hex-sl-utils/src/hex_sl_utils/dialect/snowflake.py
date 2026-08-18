from __future__ import annotations

import datetime
import re
from typing import Any, Literal

from hex_sl_utils._vendor.sqlglot import exp
from hex_sl_utils._vendor.sqlglot.dialects.dialect import map_date_part, rename_func
from hex_sl_utils._vendor.sqlglot.dialects.snowflake import (
    Snowflake as SqlGlotSnowflake,
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


class Snowflake(Dialect):
    @classmethod
    def name(cls) -> DialectName:
        return "snowflake"

    @classmethod
    def sqlglot_dialect(cls) -> str:
        return "hex-sl-snowflake"

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
        Build an IS NAN check using Snowflake's comparison approach.

        Snowflake: Similar to Postgres, NaN = NaN returns true.
        So we check: arg = 'NaN'::DOUBLE
        """

        # Cast argument to double
        cast_arg = self.cast_to_float(arg)

        # Compare with NaN literal: arg = 'NaN'::DOUBLE
        nan_literal = exp.Cast(
            this=exp.Literal.string("NaN"), to=exp.DataType.build("DOUBLE")
        )
        isnan_expr = exp.EQ(this=cast_arg.expression, expression=nan_literal)

        return TypedSelectExpression.from_sqlglot(
            isnan_expr, DataType.BOOLEAN, arg.kind
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

    def build_percentile_approx(
        self,
        arg: TypedSelectExpression,
        percentile: float,
    ) -> TypedSelectExpression:
        cast_typed = self.cast_to_float(arg)
        percentile_expr = self.func(
            "APPROX_PERCENTILE", cast_typed.expression, exp.Literal.number(percentile)
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
        Compile a literal expression with Snowflake-specific date handling.
        """

        if isinstance(literal, datetime.datetime):
            if literal.tzinfo is not None:
                final_expr = self.func(
                    "TO_TIMESTAMP_TZ",
                    exp.Literal.string(
                        literal.astimezone(datetime.timezone.utc).strftime(
                            "%Y-%m-%dT%H:%M:%S.%f"
                        )
                        + "Z"
                    ),
                )
                result = TypedSelectExpression.from_sqlglot(
                    final_expr, DataType.TIMESTAMPTZ, ExpressionKind.SCALAR
                )
            else:
                # This is a naive datetime (TIMESTAMP)
                # Use direct casting: '2023-06-15 12:30:45.000000'::TIMESTAMP
                dt_str = literal.strftime("%Y-%m-%d %H:%M:%S.%f")
                ts_expr = exp.Cast(
                    this=exp.Literal.string(dt_str), to=exp.DataType.build("TIMESTAMP")
                )
                result = TypedSelectExpression.from_sqlglot(
                    ts_expr, DataType.TIMESTAMP, ExpressionKind.SCALAR
                )

            if context is not None:
                result = self.wrap_expression_for_context(result, context)
            return result

        # Handle date objects with direct casting
        elif isinstance(literal, datetime.date) and not isinstance(
            literal, datetime.datetime
        ):
            # Use direct casting: '2023-06-15'::DATE
            date_str = literal.strftime("%Y-%m-%d")
            date_expr = exp.Cast(
                this=exp.Literal.string(date_str), to=exp.DataType.build("DATE")
            )
            result = TypedSelectExpression.from_sqlglot(
                date_expr, DataType.DATE, ExpressionKind.SCALAR
            )
            if context is not None:
                result = self.wrap_expression_for_context(result, context)
            return result

        # For all other types, use the base implementation
        return super().compile_literal(literal, context, data_type)

    def _format_timestamp_to_varchar_ff6(self, expr: exp.Expression) -> exp.Expression:
        """Format a timestamp expression to a string with microsecond precision.

        Ensures Snowflake stringification preserves microseconds. Use on TIMESTAMP or
        TIMESTAMP_NTZ expressions before concatenating a timezone suffix for
        TO_TIMESTAMP_TZ.

        Args:
            expr: The timestamp expression to format.

        Returns:
            A Snowflake SQL expression that renders the timestamp as
            'YYYY-MM-DD HH24:MI:SS.FF6'.
        """
        return self.func(
            "TO_VARCHAR", expr, exp.Literal.string("YYYY-MM-DD HH24:MI:SS.FF6")
        )

    def timestamp_subsecond_suffix(self) -> str | None:
        return ".000"

    def epoch_ms_to_timestamp(
        self, arg: TypedSelectExpression
    ) -> TypedSelectExpression:
        """
        Build expression to convert epoch milliseconds to a timestamp.
        """

        # TO_TIMESTAMP_TZ(arg, 3)
        return TypedSelectExpression.from_sqlglot(
            exp.Anonymous(
                this="TO_TIMESTAMP_TZ",
                expressions=[arg.expression, exp.Literal.number(3)],
            ),
            DataType.TIMESTAMPTZ,
            kind=arg.kind,
        )

    def cast_str_to_timestamp(
        self, arg: TypedSelectExpression, tz: str, force_tz: bool = False
    ) -> TypedSelectExpression:
        """
        Build expression to cast string to timestamp for Snowflake.
        Use TRY_CAST with requires_string=True to ensure it generates TRY_CAST
        instead of falling back to CAST.
        """
        try_cast_expr = exp.TryCast(
            this=arg.expression,
            to=exp.DataType.build("TIMESTAMP"),
            requires_string=True,
        )

        if force_tz:
            # We avoid using TIMESTAMP_TZ_FROM_PARTS here due to CUR-660.
            # First, treat the string as a TIMESTAMP_NTZ in the target timezone, and
            # then convert it to the equivalent TIMESTAMP_NTZ in UTC.
            if tz != "UTC":
                convert_tz_expr = self.func(
                    "CONVERT_TIMEZONE",
                    exp.Literal.string(
                        tz
                    ),  # Source timezone (e.g., 'America/New_York')
                    exp.Literal.string("UTC"),  # Target timezone
                    try_cast_expr,  # TRY_CAST(expression AS TIMESTAMP)
                )
            else:
                # If the timezone is already UTC, no need to change it.
                convert_tz_expr = try_cast_expr

            # Next, get its string form (microsecond precision) and add ' +00'
            # to make it an explicit TIMESTAMP_TZ string
            string_expr = self._format_timestamp_to_varchar_ff6(convert_tz_expr)
            concat_expr = exp.Concat(
                expressions=[string_expr, exp.Literal.string(" +00")]
            )

            # Now, use TO_TIMESTAMP_TZ to cast it to a timestamptz
            to_timestamp_tz_expr = self.func("TO_TIMESTAMP_TZ", concat_expr)

            # Finally, adjust the timestamptz into the target timezone, if necessary
            final_timestamp_tz_expr = to_timestamp_tz_expr
            if tz != "UTC":
                final_timestamp_tz_expr = self.func(
                    "CONVERT_TIMEZONE",
                    exp.Literal.string(tz),
                    final_timestamp_tz_expr,
                )

            return TypedSelectExpression.from_sqlglot(
                final_timestamp_tz_expr, DataType.TIMESTAMPTZ, arg.kind
            )
        else:
            ts_expr = TypedSelectExpression.from_sqlglot(
                try_cast_expr, DataType.TIMESTAMP, arg.kind
            )
            return ts_expr

    def cast_date_to_timestamptz(
        self, arg: TypedSelectExpression, tz: str
    ) -> TypedSelectExpression:
        """
        Build expression to cast a date to a timestamptz in the provided timezone.
        """
        ts = self.cast_date_to_timestamp(arg)
        return self._replace_timezone(ts, tz)

    def _try_parse_timestamp_literal(
        self, literal_value: str
    ) -> tuple[int, int, int, int, int, int, int] | None:
        """Parse a timestamp string literal into components with microseconds.

        Args:
            literal_value: String like '2021-01-02 10:00:00' or
                '2021-01-02T10:00:00.123456'

        Returns:
            Tuple of (year, month, day, hour, minute, second, microseconds) or None
            if parsing fails.
        """

        # Capture 1–6 fractional digits and pad/truncate to 6
        pattern = (
            r"^(\d{4})-(\d{1,2})-(\d{1,2})[T\s](\d{1,2}):(\d{1,2}):(\d{1,2})"
            r"(\.(\d{1,6}))?$"
        )
        match = re.match(pattern, literal_value.strip())
        if not match:
            return None

        year = int(match.group(1))
        month = int(match.group(2))
        day = int(match.group(3))
        hour = int(match.group(4))
        minute = int(match.group(5))
        second = int(match.group(6))

        if match.group(8):
            frac = match.group(8)
            microseconds = int(frac.ljust(6, "0")[:6])
        else:
            microseconds = 0

        return (year, month, day, hour, minute, second, microseconds)

    def _timestamptz_literal_from_datetime(
        self, dt: datetime.datetime
    ) -> exp.Expression:
        """Build a TIMESTAMP_TZ expression from a tz-aware datetime using an ISO 8601
        'Z' literal.

        Normalizes to UTC to avoid partition-pruning issues and keeps literals compact.
        """

        if dt.tzinfo is None:
            msg = "Expected tz-aware datetime"
            raise ValueError(msg)

        iso_utc = (
            dt.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"
        )
        return self.func("TO_TIMESTAMP_TZ", exp.Literal.string(iso_utc))

    def _replace_timezone(
        self, ts: TypedSelectExpression, tz: str
    ) -> TypedSelectExpression:
        """
        Helper to replace the timezone of a timestamp in place (without shifting the
        time)
        """

        # Special case for TRY_CAST([timestamp literal] AS timestamp)
        if isinstance(ts.expression, exp.TryCast):
            cast_arg = ts.expression.args.get("this")
            if isinstance(cast_arg, exp.Literal) and cast_arg.is_string:
                components = self._try_parse_timestamp_literal(cast_arg.this)
                if components is not None:
                    year, month, day, hour, minute, second, microseconds = components

                    # YYYY-MM-DD HH:MI:SS.FF6 for TIMESTAMP(NTZ) cast
                    timestamp_str = (
                        f"{year:04d}-{month:02d}-{day:02d} "
                        f"{hour:02d}:{minute:02d}:{second:02d}.{microseconds:06d}"
                    )

                    # If target tz is UTC, emit a single ISO 'Z' literal and return
                    if tz == "UTC":
                        iso_utc = (
                            f"{year:04d}-{month:02d}-{day:02d}"
                            f"T{hour:02d}:{minute:02d}:{second:02d}.{microseconds:06d}Z"
                        )
                        tz_expr = self.func(
                            "TO_TIMESTAMP_TZ", exp.Literal.string(iso_utc)
                        )
                        return TypedSelectExpression.from_sqlglot(
                            tz_expr, DataType.TIMESTAMPTZ, kind=ts.kind
                        )

                    # Else: keep existing dynamic path with timezone math in Snowflake
                    ts_cast = exp.Cast(
                        this=exp.Literal.string(timestamp_str),
                        to=exp.DataType.build("TIMESTAMP"),
                    )
                    utc_expr = self.func(
                        "CONVERT_TIMEZONE",
                        exp.Literal.string(tz),
                        exp.Literal.string("UTC"),
                        ts_cast,
                    )
                    string_expr = self._format_timestamp_to_varchar_ff6(utc_expr)
                    concat_expr = exp.Concat(
                        expressions=[string_expr, exp.Literal.string("Z")]
                    )
                    utc_timestamptz = self.func("TO_TIMESTAMP_TZ", concat_expr)

                    tz_expr = self.func(
                        "CONVERT_TIMEZONE", exp.Literal.string(tz), utc_timestamptz
                    )
                    return TypedSelectExpression.from_sqlglot(
                        tz_expr, DataType.TIMESTAMPTZ, kind=ts.kind
                    )

        # General case: treat naive timestamp as being in target timezone and convert to
        # UTC
        general_utc_expr: exp.Expression
        if tz != "UTC":
            general_utc_expr = self.func(
                "CONVERT_TIMEZONE",
                exp.Literal.string(tz),  # Source timezone (target timezone)
                exp.Literal.string("UTC"),  # Target timezone (UTC)
                ts.expression,
            )
        else:
            # Already in UTC
            general_utc_expr = ts.expression

        # Convert to string (microsecond precision) and add UTC timezone offset
        string_expr = self._format_timestamp_to_varchar_ff6(general_utc_expr)
        concat_expr = exp.Concat(expressions=[string_expr, exp.Literal.string("Z")])

        # Use TO_TIMESTAMP_TZ to create timestamptz in UTC
        utc_timestamptz = self.func("TO_TIMESTAMP_TZ", concat_expr)

        # Convert back to target timezone for final result
        if tz != "UTC":
            final_expr = self.func(
                "CONVERT_TIMEZONE",
                exp.Literal.string(tz),
                utc_timestamptz,
            )
        else:
            final_expr = utc_timestamptz

        return TypedSelectExpression.from_sqlglot(
            final_expr,
            DataType.TIMESTAMPTZ,
            kind=ts.kind,
        )

    def datetime_to_epoch_ms(self, arg: TypedSelectExpression) -> TypedSelectExpression:
        if arg.data_type == DataType.TIMESTAMPTZ:
            # Always convert to UTC before extracting epoch millis
            arg = self.at_timezone(arg, "UTC")

        epoch_expr: exp.Expression
        if arg.data_type == DataType.DATE:
            epoch_expr = exp.Mul(
                this=self.func(
                    "DATE_PART", exp.Literal.string("epoch_second"), arg.expression
                ),
                expression=exp.Literal.number(1000),
            )
        else:
            epoch_expr = self.func(
                "DATE_PART", exp.Literal.string("epoch_millisecond"), arg.expression
            )

        return TypedSelectExpression.from_sqlglot(
            epoch_expr,
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
        if unit == "week" or unit == "weekmonday":
            expr = self._trunc_week(arg, unit, convert_tz)
        elif unit not in self._DATE_UNITS:
            expr = self._trunc_time_general(arg, unit)
        else:
            expr = self._trunc_date_general(arg, unit, convert_tz)

        return TypedSelectExpression.from_sqlglot(
            expr,
            DataType.TIMESTAMPTZ if convert_tz is not None else DataType.TIMESTAMP,
            kind=arg.kind,
        )

    def _trunc_date_general(
        self,
        arg: TypedSelectExpression,
        unit: TimeTruncUnit,
        convert_tz: str | None,
    ) -> exp.Expression:
        """
        Implements general date truncation for Snowflake for all units except 'week'.

        The generated SQL will look like one of these, depending on whether a
        timezone is provided:

        Without timezone:
        DATE_TRUNC('<unit>', <expression>)

        With timezone:
        DATE_TRUNC('<unit>', CONVERT_TIMEZONE('<timezone>', <expression>))

        Args:
            arg: The expression representing the date/time to be truncated.
            unit: The unit to truncate to (e.g., 'year', 'month', 'day', 'hour', etc.).
            convert_tz: The timezone to be used for the truncation, if any.

        Returns:
            exp.Expression: A new expression representing the truncated
                            date/time.
        """

        # Build the DATE_TRUNC function call
        tz_expr: exp.Expression
        if convert_tz:
            # Convert to desired timezone then remove timezone
            tz_expr = exp.cast(
                self.func(
                    "CONVERT_TIMEZONE", exp.Literal.string(convert_tz), arg.expression
                ),
                exp.DataType.build("TIMESTAMP_NTZ"),
            )
        else:
            tz_expr = arg.expression

        date_trunc_expr = self.func("DATE_TRUNC", exp.Literal.string(unit), tz_expr)

        if convert_tz:
            # Convert back to timezone aware timestamp
            date_trunc_expr = self.func(
                "CONVERT_TIMEZONE",
                exp.Literal.string(convert_tz),
                exp.Literal.string("UTC"),
                date_trunc_expr,
            )
        return date_trunc_expr

    def _trunc_time_general(
        self, arg: TypedSelectExpression, unit: TimeTruncUnit
    ) -> exp.Expression:
        """
        Implements general time truncation for Snowflake.

        When truncating to units of hour or smaller, we never need to convert timezones

        The generated SQL will look like this:

        DATE_TRUNC('<unit>', <expression>)

        Args:
            arg: The expression representing the date/time to be truncated.
            unit: The unit to truncate to (e.g., 'year', 'month', 'day', 'hour', etc.).
            convert_tz: The timezone to be used for the truncation, if any.

        Returns:
            exp.Expression: A new expression representing the truncated
                            date/time.
        """
        date_trunc_expr = self.func(
            "DATE_TRUNC", exp.Literal.string(unit), arg.expression
        )
        return date_trunc_expr

    def _trunc_week(
        self,
        arg: TypedSelectExpression,
        unit: Literal["week", "weekmonday"],
        convert_tz: str | None,
    ) -> exp.Expression:
        """
        Implements week truncation for Snowflake, truncating to Sunday or Monday

        This is tricky, becuase snowflake provides a WEEK_START setting that controls
        the start of the week, and we need to truncate regardless
        of the value of this setting.

        This method works as follows:
            1. It determines Snowflake's current WEEK_START setting by using a
               reference date (2012-01-08) and checking which day of the week it
               truncates to.
            2. It then uses this information to adjust the input date before and
               after truncation to ensure we always truncate approriately

        The core logic is equivalent to this SQL:
        DATEADD(day, -first_day_of_week,
            DATE_TRUNC(
                week,
                DATEADD(
                    day,
                    first_day_of_week,
                    input_date
                )
            )
        )

        For weeks starting on Sunday, first_day_of_week is:
        MOD(DAYOFWEEKISO(DATE_TRUNC('week', '2012-01-08'::date)), 7)

        For weeks starting on Monday, first_day_of_week is:
        MOD(DAYOFWEEKISO(DATE_TRUNC('week', '2012-01-08'::date)) - 1, 7)

        This expression returns:

        | WEEK_START | weeks starting on Sunday | weeks starting on Monday |
        |------------|--------------------------|--------------------------|
        | Sunday     | 0                        | 7                        |
        | Monday     | 1                        | 0                        |
        | Tuesday    | 2                        | 1                        |
        | ...        | ...                      | ...                      |


        By adding this value before truncation and subtracting it after, we can make
        sure to always truncate appropriately

        Args:
            arg: The expression representing the date to be truncated.
            unit: "week" to truncate to Sunday or "weekmonday" to truncate to Monday
            convert_tz: The timezone to be used for the truncation, if any.

        Returns:
            exp.Expression: A new expression representing the date truncated
                           to the start of the week
        """

        # Determine the first day of week in Snowflake

        ref_dt_day_of_week_sun = self.func(
            "DAYOFWEEKISO",
            self.func(
                "DATE_TRUNC",
                exp.Literal.string("week"),
                exp.Cast(
                    this=exp.Literal.string("2012-01-08"),
                    to=exp.DataType.build("DATE"),
                ),
            ),
        )
        ref_dt_day_of_week_mon = exp.Sub(
            this=ref_dt_day_of_week_sun, expression=exp.Literal.number(1)
        )
        first_day_of_week = self.func(
            "MOD",
            ref_dt_day_of_week_sun if unit == "week" else ref_dt_day_of_week_mon,
            exp.Literal.number(7),
        )

        # Build the complex week truncation expression
        tz_expr: exp.Expression
        if convert_tz:
            # Convert to desired timezone then remove timezone
            tz_expr = exp.cast(
                self.func(
                    "CONVERT_TIMEZONE", exp.Literal.string(convert_tz), arg.expression
                ),
                exp.DataType.build("TIMESTAMP_NTZ"),
            )
        else:
            tz_expr = arg.expression

        week_trunc_expr = self.func(
            "DATEADD",
            exp.Literal.string("day"),
            exp.Neg(this=first_day_of_week),
            self.func(
                "DATE_TRUNC",
                exp.Literal.string("week"),
                self.func(
                    "DATEADD", exp.Literal.string("day"), first_day_of_week, tz_expr
                ),
            ),
        )

        if convert_tz:
            # Convert back to timezone aware timestamp
            week_trunc_expr = self.func(
                "CONVERT_TIMEZONE",
                exp.Literal.string(convert_tz),
                exp.Literal.string("UTC"),
                week_trunc_expr,
            )

        return week_trunc_expr

    def at_timezone(self, arg: TypedSelectExpression, tz: str) -> TypedSelectExpression:
        if arg.data_type == DataType.TIMESTAMP:
            return self._replace_timezone(arg, tz)
        else:
            return TypedSelectExpression.from_sqlglot(
                exp.Anonymous(
                    this="convert_timezone",
                    expressions=[exp.Literal.string(tz), arg.expression],
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
        Snowflake has a built-in SPLIT_PART function, with slightly
        different semantics about out of bounds indexes.
        """

        kind = ExpressionKind._validate_infer_kind(
            [
                string.kind,
                delimiter.kind,
                part_number.kind,
            ]
        )
        return TypedSelectExpression.from_sqlglot(
            exp.Anonymous(
                this="SPLIT_PART",
                expressions=[
                    string.expression,
                    delimiter.expression,
                    part_number.expression,
                ],
            ),
            DataType.STRING,
            kind,
        )

    def startswith(
        self, string: TypedSelectExpression, prefix: TypedSelectExpression
    ) -> TypedSelectExpression:
        """
        Snowflake-specific startswith implementation using native STARTSWITH function.
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
        Snowflake-specific endswith implementation using native ENDSWITH function.
        """

        kind = ExpressionKind._validate_infer_kind([string.kind, suffix.kind])
        endswith_expr = self.func("ENDSWITH", string.expression, suffix.expression)
        return TypedSelectExpression.from_sqlglot(endswith_expr, DataType.BOOLEAN, kind)

    def concat(self, *args: TypedSelectExpression) -> TypedSelectExpression:
        """
        Build a CONCAT expression that treats NULLs as empty strings for Snowflake.

        Snowflake's CONCAT returns NULL if any argument is NULL, so we need to wrap
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

        # Snowflake has a native CONTAINS function
        contains_expr = self.func("CONTAINS", string.expression, substring.expression)

        return TypedSelectExpression.from_sqlglot(contains_expr, DataType.BOOLEAN, kind)

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

        # Use DATE_PART function
        extract_expr: exp.Expression
        if unit == "millisecond":
            # Use epoch_millisecond and modulo 1000
            date_part_expr = self.func(
                "DATE_PART", exp.Literal.string("epoch_millisecond"), arg.expression
            )
            extract_expr = exp.Mod(
                this=date_part_expr, expression=exp.Literal.number(1000)
            )
        else:
            # Snowflake uses lowercase unit names in DATE_PART
            date_part_expr = self.func(
                "DATE_PART", exp.Literal.string(unit.lower()), arg.expression
            )

            # Cast to int for seconds since these are fractional in some dialects
            if unit == "second":
                extract_expr = exp.Cast(
                    this=date_part_expr, to=exp.DataType.build("BIGINT")
                )
            else:
                extract_expr = date_part_expr

        return TypedSelectExpression.from_sqlglot(
            extract_expr, DataType.NUMBER, arg.kind
        )

    def cast_str_to_number(self, arg: TypedSelectExpression) -> TypedSelectExpression:
        """
        Build expression to cast string to number for Snowflake.
        Use TRY_CAST with requires_string=True to ensure it generates TRY_CAST
        instead of falling back to CAST.
        """

        try_cast_expr = exp.TryCast(
            this=arg.expression, to=exp.DataType.build("DOUBLE"), requires_string=True
        )
        return TypedSelectExpression.from_sqlglot(
            try_cast_expr, DataType.NUMBER, arg.kind
        )

    def cast_str_to_date(self, arg: TypedSelectExpression) -> TypedSelectExpression:
        """
        Build expression to cast string to date for Snowflake.
        Use TRY_CAST with requires_string=True to ensure it generates TRY_CAST
        instead of falling back to CAST.
        """

        try_cast_expr = exp.TryCast(
            this=arg.expression, to=exp.DataType.build("DATE"), requires_string=True
        )
        return TypedSelectExpression.from_sqlglot(
            try_cast_expr, DataType.DATE, arg.kind
        )


class SnowflakeSqlGlotOverride(SqlGlotSnowflake):
    @classmethod
    def dialect_name(cls) -> str:
        return "hex-sl-snowflake"

    class Generator(PlaceholderGeneratorMixin, SqlGlotSnowflake.Generator):
        def placeholder_sql(self, expression: exp.Placeholder) -> str:
            return placeholder_sql(self, expression)

        # From ibis
        TRANSFORMS = SqlGlotSnowflake.Generator.TRANSFORMS.copy() | {
            exp.ApproxDistinct: rename_func("approx_count_distinct"),
            exp.Levenshtein: rename_func("editdistance"),
        }

        def values_sql(
            self, expression: exp.Values, values_as_table: bool = True
        ) -> str:
            # snowflake supports VALUES syntax, but not all expressions are
            # valid there, so it's easier to just use UNION ALL instead.
            return super().values_sql(expression, values_as_table=False)

    class Parser(SqlGlotSnowflake.Parser):
        FUNCTION_PARSERS = SqlGlotSnowflake.Parser.FUNCTION_PARSERS.copy()
        # Override DATE_PART parser to ensure time units are parsed as Var nodes
        FUNCTION_PARSERS["DATE_PART"] = lambda self: self._parse_date_part_hexsl()

        PLACEHOLDER_PARSERS = placeholder_parser_mapping(
            SqlGlotSnowflake.Parser.PLACEHOLDER_PARSERS,
            parameter_fallback=lambda self: (
                self.expression(exp.Placeholder, this=getattr(self._prev, "text", ""))
                if self._match(TokenType.NUMBER) or self._match_set(self.ID_VAR_TOKENS)
                else None
            ),
        )

        def _parse_placeholder(self) -> exp.Expression | None:
            return parse_jinja_placeholder(self)

        def _parse_date_part_hexsl(self) -> exp.Expression | None:
            """
            Custom DATE_PART parser that creates Extract expressions with Var
            time units.

            This ensures time units (YEAR, MONTH, epoch_millisecond, etc.) are parsed
            as Var nodes rather than Column nodes, preventing add_table_qualifiers()
            from incorrectly qualifying them. It also preserves precision for epoch
            units by avoiding the standard parser's TimeToUnix conversion.
            """
            # Parse time unit as var/identifier
            this = self._parse_var() or self._parse_type()
            if not this:
                return None

            self._match_text_seq(",")  # type: ignore[no-untyped-call]
            expression = self._parse_bitwise()

            # Map date part abbreviations (Y -> YEAR, etc.)

            mapped_this = map_date_part(this)

            # Return Extract expression with Var time unit
            return self.expression(exp.Extract, this=mapped_this, expression=expression)
