from __future__ import annotations

import datetime
import math
from typing import Any, ClassVar, Literal

from hex_sl_utils._vendor.sqlglot import exp
from hex_sl_utils.datatype import DataType, datatype_to_sqlglot
from hex_sl_utils.dialect.dialect_name import DialectName, normalize_dialect_name
from hex_sl_utils.exception import UnsupportedByDialectError
from hex_sl_utils.expr import ExpressionContext, ExpressionKind, TypedSelectExpression
from hex_sl_utils.expr.expr_substitution import _needs_parens_for_substitution
from hex_sl_utils.time import TimeTruncUnit
from hex_sl_utils.utils import assert_unreachable

# Time part units for the time_part function
TimePartUnit = Literal["hour", "minute", "second", "millisecond"]


class Dialect:
    _DATE_UNITS = frozenset(["year", "quarter", "month", "week", "weekmonday", "day"])

    @classmethod
    def name(cls) -> DialectName:
        """
        Returns the name of this dialect.
        e.g. "duckdb"

        Returns:
            str: The name of the dialect.
        """
        msg = "Subclass must implement this method"
        raise NotImplementedError(msg)

    @classmethod
    def title_line(cls) -> str:
        """
        Returns a prominent title line of this dialect
        e.g. "DuckDB"
        """
        return f"========[{cls.name().upper()}]========="

    @classmethod
    def sqlglot_dialect(cls) -> str:
        """
        Returns the sqlglot dialect name for this dialect.
        e.g. "duckdb"

        Returns:
            str: The sqlglot dialect name.
        """
        msg = "Subclass must implement this method"
        raise NotImplementedError(msg)

    def supports_inequality_joins(self) -> bool:
        """
        Determine if the dialect supports inequality joins.
        """
        return True

    def supports_groupby_by_index(self) -> bool:
        """
        Determine if the dialect supports groupby using numeric index of selection
        expressions.

        e.g. `SELECT origin, avg(distance) FROM flights GROUP BY 1`
        """
        return True

    def supports_window_partition_by_alias(self) -> bool:
        """
        Returns True if this dialect allows using column aliases in the PARTITION BY
        clause of window functions. If False, must use original column expressions.

        Some dialects (like SQL Server) require using the original expressions rather
        than aliases in window function partitions.
        """
        return True

    def quote(self, identifier: str) -> str:
        """
        Quote an identifier according to this dialect's quoting rules.

        Args:
            identifier: The identifier to quote (column, table, etc.)

        Returns:
            str: The quoted identifier
        """

        # Create an identifier expression and convert to SQL for this dialect
        id_expr = exp.to_identifier(identifier, quoted=True)
        return id_expr.sql(dialect=self.sqlglot_dialect())

    def truncates_on_integer_division(self) -> bool:
        """
        Determine if the dialect performs truncation on integer division.
        """
        msg = "Subclass must implement this method"
        raise NotImplementedError(msg)

    def mod_supports_floats(self) -> bool:
        """
        Determine if the dialect supports floating point numbers for the modulus
        operator

        If not, then numbers must be casted to integers or decimals before the
        modulus operator is applied.
        """
        msg = "Subclass must implement this method"
        raise NotImplementedError(msg)

    def supports_median(self) -> bool:
        """
        Determine if the dialect supports the median agg function.
        """
        msg = "Subclass must implement this method"
        raise NotImplementedError(msg)

    def supports_percentile_exact(self) -> bool:
        """Determine if the dialect supports exact percentile aggregations."""
        return False

    def supports_percentile_approx(self) -> bool:
        """Determine if the dialect supports approximate percentile aggregations."""
        return False

    def build_percentile_exact(
        self,
        arg: TypedSelectExpression,
        percentile: float,
    ) -> TypedSelectExpression:
        """Build an exact percentile aggregation expression for the dialect."""
        msg = "exact percentile is not supported"
        raise UnsupportedByDialectError(msg)

    def build_percentile_approx(
        self,
        arg: TypedSelectExpression,
        percentile: float,
    ) -> TypedSelectExpression:
        """Build an approximate percentile aggregation expression for the dialect."""
        msg = "approximate percentile is not supported"
        raise UnsupportedByDialectError(msg)

    def truncate_cte_name(self, cte_name: str) -> str:
        """
        Truncate CTE name if needed for dialect-specific limits.

        Most dialects have no limit, so the default implementation returns
        the name unchanged. Dialects with limits should override this method.

        Args:
            cte_name: The CTE name to potentially truncate

        Returns:
            The CTE name, possibly truncated to meet dialect limits
        """
        return cte_name

    def supports_non_finite_floats(self) -> bool:
        """
        Determine if the dialect supports non-finite floating point numbers.
        """
        msg = "Subclass must implement this method"
        raise NotImplementedError(msg)

    def supports_cot_function(self) -> bool:
        """
        Determine if the dialect supports the native COT function.
        """
        return True

    def null_literals_should_be_cast_to_type(self) -> bool:
        """
        Determine if the dialect requires explicit casts for null literals.
        """
        return False

    def use_empty_over_for_count_star_window_function(self) -> bool:
        """
        Should an empty window clause be used when count(*) is used in a
        window function.

        e.g. `SELECT count(*) OVER ()`
        """
        return False

    def epoch_ms_to_timestamp(
        self,
        arg: TypedSelectExpression,
    ) -> TypedSelectExpression:
        """
        Build expression to convert epoch milliseconds to a timestamp.
        """

        # Cast to int first if needed
        int_expr = exp.Cast(this=arg.expression, to=exp.DataType.build("BIGINT"))

        # Convert milliseconds to timestamp - using FROM_UNIXTIME with milliseconds
        # Divide by 1000 to get seconds
        seconds_expr = exp.Div(this=int_expr, expression=exp.Literal.number(1000))
        timestamp_expr = self.func("FROM_UNIXTIME", seconds_expr)

        naive_ts = TypedSelectExpression.from_sqlglot(
            timestamp_expr, DataType.TIMESTAMP, arg.kind
        )
        return self.at_timezone(naive_ts, "UTC")

    def datetime_to_epoch_ms(self, arg: TypedSelectExpression) -> TypedSelectExpression:
        """
        Build expression to convert a timestamp to epoch milliseconds.
        """

        if arg.data_type == DataType.TIMESTAMPTZ:
            # Always convert to UTC before extracting epoch millis
            arg = self.at_timezone(arg, "UTC")

        # Get epoch seconds using UNIX_TIMESTAMP or similar
        epoch_seconds = self.func("UNIX_TIMESTAMP", arg.expression)

        # Multiply by 1000 to get milliseconds
        thousand = exp.Literal.number(1000)
        epoch_ms = exp.Mul(this=epoch_seconds, expression=thousand)

        # Floor the result
        floored = exp.Floor(this=epoch_ms)

        return TypedSelectExpression.from_sqlglot(floored, DataType.NUMBER, arg.kind)

    def datetime_trunc(
        self,
        arg: TypedSelectExpression,
        unit: TimeTruncUnit,
        tz: str,
    ) -> TypedSelectExpression:
        """
        Build expression to truncate a date or timestamp to a given unit.
        """
        msg = "Subclass must implement this method"
        raise NotImplementedError(msg)

    # Builder methods with default implementations
    def cast_str_to_timestamp(
        self, arg: TypedSelectExpression, tz: str, force_tz: bool = False
    ) -> TypedSelectExpression:
        """
        Build expression to cast string to timestamp, or null if the string is not
        a timestamp.

        A value of time TIMESTAMP should be returned if possible, but if the dialect
        only supports parsing string to timezone aware timestamps, then the
        provided timezone should be used.
        """

        try_cast_expr = exp.TryCast(
            this=arg.expression, to=exp.DataType.build("TIMESTAMP")
        )
        ts_expr = TypedSelectExpression.from_sqlglot(
            try_cast_expr, DataType.TIMESTAMP, arg.kind
        )

        if force_tz:
            ts_expr = self.at_timezone(ts_expr, tz)
            return TypedSelectExpression.from_sqlglot(
                ts_expr.expression, DataType.TIMESTAMPTZ, kind=ts_expr.kind
            )
        else:
            return ts_expr

    def cast_str_to_date(self, arg: TypedSelectExpression) -> TypedSelectExpression:
        """
        Build expression to cast string to date, or null if the string is
        not a date
        """

        try_cast_expr = exp.TryCast(this=arg.expression, to=exp.DataType.build("DATE"))
        return TypedSelectExpression.from_sqlglot(
            try_cast_expr, DataType.DATE, arg.kind
        )

    def cast_timestamptz_to_date(
        self, arg: TypedSelectExpression, tz: str
    ) -> TypedSelectExpression:
        """
        Build expression to cast timestamptz to date, or null if the timestamptz is
        not a date
        """

        # Convert to target timezone first
        tz_arg = self.at_timezone(arg, tz)
        cast_expr = exp.Cast(this=tz_arg.expression, to=exp.DataType.build("DATE"))
        return TypedSelectExpression.from_sqlglot(cast_expr, DataType.DATE, arg.kind)

    def cast_timestamp_to_date(
        self, arg: TypedSelectExpression
    ) -> TypedSelectExpression:
        """
        Build expression to cast timestamp to date, or null if the timestamp is
        not a date
        """

        cast_expr = exp.Cast(this=arg.expression, to=exp.DataType.build("DATE"))
        return TypedSelectExpression.from_sqlglot(cast_expr, DataType.DATE, arg.kind)

    def cast_date_to_timestamp(
        self, arg: TypedSelectExpression
    ) -> TypedSelectExpression:
        """
        Build expression to cast a date to a naive timestamp
        """

        cast_expr = exp.Cast(this=arg.expression, to=exp.DataType.build("TIMESTAMP"))
        return TypedSelectExpression.from_sqlglot(
            cast_expr, DataType.TIMESTAMP, arg.kind
        )

    def cast_date_to_timestamptz(
        self, arg: TypedSelectExpression, tz: str
    ) -> TypedSelectExpression:
        """
        Build expression to cast a date to a timestamptz in the provided timezone.
        """
        return self.at_timezone(self.cast_date_to_timestamp(arg), tz)

    def cast_str_to_number(self, arg: TypedSelectExpression) -> TypedSelectExpression:
        """
        Build expression to cast string to number, or null if the string is
        not a number
        """

        try_cast_expr = exp.TryCast(
            this=arg.expression, to=exp.DataType.build("DOUBLE")
        )
        return TypedSelectExpression.from_sqlglot(
            try_cast_expr, DataType.NUMBER, arg.kind
        )

    def cast_to_float(self, arg: TypedSelectExpression) -> TypedSelectExpression:
        """
        Cast expression to float/double type.

        Can be overridden by dialects that need special handling (e.g., ClickHouse).
        """

        cast_expr = exp.Cast(this=arg.expression, to=exp.DataType.build("DOUBLE"))
        return TypedSelectExpression.from_sqlglot(cast_expr, DataType.NUMBER, arg.kind)

    def cast_to_int(self, arg: TypedSelectExpression) -> TypedSelectExpression:
        """
        Cast expression to integer type.

        Can be overridden by dialects that need special handling (e.g., ClickHouse).
        """

        cast_expr = exp.Cast(this=arg.expression, to=exp.DataType.build("INT"))
        return TypedSelectExpression.from_sqlglot(cast_expr, DataType.NUMBER, arg.kind)

    def cast_to_string(self, arg: TypedSelectExpression) -> TypedSelectExpression:
        """
        Cast expression to string type.

        Can be overridden by dialects that need special handling (e.g., ClickHouse).
        """

        cast_expr = exp.Cast(this=arg.expression, to=exp.DataType.build("VARCHAR"))
        return TypedSelectExpression.from_sqlglot(cast_expr, DataType.STRING, arg.kind)

    # Timezone aware date part functions
    def at_timezone(self, arg: TypedSelectExpression, tz: str) -> TypedSelectExpression:
        """
        Build expression to attach a timezone to a timezone-unaware timestamp, or
        convert a timestamptz to a different timezone

        The resulting expression may be either a timestamp or timestamptz, depending
        on the dialect.
        """
        msg = "Subclass must implement at_timezone method"
        raise NotImplementedError(msg)

    def date_part(
        self,
        arg: TypedSelectExpression,
        unit: Literal["year", "quarter", "month", "day"],
        timezone: str,
    ) -> TypedSelectExpression:
        """
        Build expression to extract a date part from a timestamp.
        """

        if arg.data_type == DataType.TIMESTAMPTZ:
            arg = self.at_timezone(arg, timezone)

        # Use EXTRACT function
        # exp.Var represents unquoted identifiers,
        # correct for EXTRACT units like YEAR, MONTH
        unit_expr = exp.Var(this=unit.upper())

        extract_expr = exp.Extract(this=unit_expr, expression=arg.expression)

        return TypedSelectExpression.from_sqlglot(
            extract_expr, DataType.NUMBER, arg.kind
        )

    def day_of_week_part(
        self,
        arg: TypedSelectExpression,
        timezone: str,
    ) -> TypedSelectExpression:
        if arg.data_type == DataType.TIMESTAMPTZ:
            arg = self.at_timezone(arg, timezone)

        # Get day of week using EXTRACT('dow' FROM date) which is standard SQL
        # EXTRACT('dow') returns Sunday=0, Saturday=6, so add 1 to get Sunday=1,
        # Saturday=7
        dow_expr = exp.Extract(
            this=exp.Identifier(this="dow"), expression=arg.expression
        )
        dow_plus_one = exp.Add(this=dow_expr, expression=exp.Literal.number(1))

        return TypedSelectExpression.from_sqlglot(
            dow_plus_one, DataType.NUMBER, arg.kind
        )

    def time_part(
        self,
        arg: TypedSelectExpression,
        unit: TimePartUnit,
        timezone: str,
    ) -> TypedSelectExpression:
        if arg.data_type == DataType.DATE:
            # Dates don't have a time part, so we return 0
            return self.compile_literal(0)

        if arg.data_type == DataType.TIMESTAMPTZ:
            arg = self.at_timezone(arg, timezone)

        # Use EXTRACT function
        if unit == "millisecond":
            # Milliseconds need special handling since EXTRACT milliseconds returns
            # "The seconds field, including fractional parts, multiplied by 1000."
            # so we extract millisecond and modulo 1000
            extract_expr = exp.Extract(
                this=exp.Identifier(this=unit.upper()), expression=arg.expression
            )
            mod_expr = exp.Mod(this=extract_expr, expression=exp.Literal.number(1000))
            return TypedSelectExpression.from_sqlglot(
                mod_expr, DataType.NUMBER, arg.kind
            )
        else:
            # Use uppercase unit name directly, like date_part does
            extract_expr = exp.Extract(
                this=exp.Identifier(this=unit.upper()), expression=arg.expression
            )

            # Cast to int for seconds since these are fractional in some dialects
            if unit == "second":
                cast_expr = self.cast_to_int(
                    TypedSelectExpression.from_sqlglot(
                        extract_expr, DataType.NUMBER, arg.kind
                    )
                )
                return cast_expr

            return TypedSelectExpression.from_sqlglot(
                extract_expr, DataType.NUMBER, arg.kind
            )

    def date_diff(
        self,
        arg0: TypedSelectExpression,
        arg1: TypedSelectExpression,
        diff_fn: Literal[
            "diffweeks",
            "diffdays",
            "diffhours",
            "diffminutes",
            "diffseconds",
            "diffmilliseconds",
        ],
        timezone: str,
    ) -> TypedSelectExpression:
        """
        Build expression to calculate the difference between two dates.
        """

        epoch0 = self.datetime_to_epoch_ms(arg0)
        epoch1 = self.datetime_to_epoch_ms(arg1)
        kind = ExpressionKind._validate_infer_kind([epoch0.kind, epoch1.kind])

        if diff_fn == "diffweeks":
            unit_millis = 7 * 24 * 60 * 60 * 1000
        elif diff_fn == "diffdays":
            unit_millis = 24 * 60 * 60 * 1000
        elif diff_fn == "diffhours":
            unit_millis = 60 * 60 * 1000
        elif diff_fn == "diffminutes":
            unit_millis = 60 * 1000
        elif diff_fn == "diffseconds":
            unit_millis = 1000
        elif diff_fn == "diffmilliseconds":
            unit_millis = 1
        else:
            assert_unreachable(diff_fn)

        # Calculate (epoch1 - epoch0) / unit_millis
        diff_expr = exp.Sub(this=epoch1.expression, expression=epoch0.expression)
        divisor = exp.Literal.number(float(unit_millis))
        result_expr = exp.Div(this=exp.Paren(this=diff_expr), expression=divisor)

        return TypedSelectExpression.from_sqlglot(result_expr, DataType.NUMBER, kind)

    def now(self, timezone: str) -> TypedSelectExpression:
        """
        Build expression to get the current timestamp.

        Defaults to sqlglot's CurrentTimestamp function, and returns
        a timestamp with timezone.
        """

        return TypedSelectExpression.from_sqlglot(
            exp.CurrentTimestamp(),
            DataType.TIMESTAMPTZ,
            kind=ExpressionKind.SCALAR,
        )

    def today(self, timezone: str) -> TypedSelectExpression:
        """
        Build expression to get the current date.

        Defaults to sqlglot's CurrentDate function, and returns
        a date.
        """

        return TypedSelectExpression.from_sqlglot(
            exp.CurrentDate(),
            DataType.DATE,
            kind=ExpressionKind.SCALAR,
        )

    def contains(
        self, string: TypedSelectExpression, substring: TypedSelectExpression
    ) -> TypedSelectExpression:
        """
        Build expression to check if a string contains a substring.

        Default implementation uses STRPOS/POSITION which is available in most dialects.
        Dialects can override this for dialect-specific implementations.
        """

        kind = ExpressionKind._validate_infer_kind([string.kind, substring.kind])

        # Use STRPOS(string, substring) > 0
        strpos_expr = self.func("STRPOS", string.expression, substring.expression)
        contains_expr = exp.GT(this=strpos_expr, expression=exp.Literal.number(0))

        return TypedSelectExpression.from_sqlglot(contains_expr, DataType.BOOLEAN, kind)

    def startswith(
        self, string: TypedSelectExpression, prefix: TypedSelectExpression
    ) -> TypedSelectExpression:
        """
        Build expression to check if a string starts with a substring.

        Uses LEFT(string, LENGTH(prefix)) = prefix approach which is safe
        for column references and doesn't require escaping special characters.
        """

        kind = ExpressionKind._validate_infer_kind([string.kind, prefix.kind])

        # Use LEFT(string, LENGTH(prefix)) = prefix
        prefix_length = exp.Length(this=prefix.expression)
        left_expr = exp.Left(this=string.expression, expression=prefix_length)
        eq_expr = exp.EQ(this=left_expr, expression=prefix.expression)

        return TypedSelectExpression.from_sqlglot(eq_expr, DataType.BOOLEAN, kind)

    def endswith(
        self, string: TypedSelectExpression, suffix: TypedSelectExpression
    ) -> TypedSelectExpression:
        """
        Build expression to check if a string ends with a substring.

        Uses RIGHT(string, LENGTH(suffix)) = suffix approach which is safe
        for column references and doesn't require escaping special characters.
        """

        kind = ExpressionKind._validate_infer_kind([string.kind, suffix.kind])

        # Use RIGHT(string, LENGTH(suffix)) = suffix
        suffix_length = exp.Length(this=suffix.expression)
        right_expr = exp.Right(this=string.expression, expression=suffix_length)
        eq_expr = exp.EQ(this=right_expr, expression=suffix.expression)

        return TypedSelectExpression.from_sqlglot(eq_expr, DataType.BOOLEAN, kind)

    def str_length(self, string: TypedSelectExpression) -> TypedSelectExpression:
        """
        Build expression to get the length of a string.

        Uses standard LENGTH function. Dialects can override for special handling.
        """

        kind = string.kind
        length_expr = exp.Length(this=string.expression)

        return TypedSelectExpression.from_sqlglot(length_expr, DataType.NUMBER, kind)

    def splitpart(
        self,
        string: TypedSelectExpression,
        delimiter: TypedSelectExpression,
        part_number: TypedSelectExpression,
    ) -> TypedSelectExpression:
        """
        Build an expression which splits a given string on a specified
        substring and returns the requested part (1-indexed). If the string
        is null, the result is null. If the part number is out of range, the
        result is the empty string.

        Defaults to using SPLIT combined with array indexing,
        which will work if the DB supports arrays.
        """

        kind = ExpressionKind._validate_infer_kind(
            [
                string.kind,
                delimiter.kind,
                part_number.kind,
            ]
        )

        # Split the string into an array
        split_expr = exp.Split(this=string.expression, expression=delimiter.expression)

        # Convert 1-based part_number to 0-based index
        part_index = exp.Sub(
            this=exp.Cast(this=part_number.expression, to=exp.DataType.build("INT")),
            expression=exp.Literal.number(1),
        )

        # Access the array element - sqlglot will handle dialect-specific
        # index adjustment
        array_access = exp.Bracket(this=split_expr, expressions=[part_index])

        # Wrap with COALESCE to return empty string if out of bounds
        coalesce_expr = exp.Coalesce(
            this=array_access, expressions=[exp.Literal.string("")]
        )

        # Handle null string case with CASE WHEN
        result_expr = exp.Case(
            ifs=[
                exp.If(
                    this=exp.Is(this=string.expression, expression=exp.Null()),
                    true=exp.Null(),
                )
            ],
            default=coalesce_expr,
        )

        return TypedSelectExpression.from_sqlglot(result_expr, DataType.STRING, kind)

    def timestamp_subsecond_suffix(self) -> str | None:
        """
        Returns the suffix the dialect appends when converting timestamps to
        strings that have no fractional component. Most dialects don't add
        a suffix like ".000000", but some like mssql do.
        """
        return None

    def cast_timestamp_to_string(
        self, arg: TypedSelectExpression
    ) -> TypedSelectExpression:
        """
        Cast a timestamp to string.

        Base implementation uses CAST to VARCHAR with optional REPLACE to remove
        fractional seconds suffix. Dialects can override this method for special
        handling (e.g., ClickHouse can cast to DateTime first) or just override
        timestamp_subsecond_suffix() to specify the suffix to remove.
        """

        # First cast to VARCHAR
        cast_expr = exp.Cast(this=arg.expression, to=exp.DataType.build("VARCHAR"))

        # Then use REPLACE to remove the fractional seconds suffix if specified
        suffix = self.timestamp_subsecond_suffix()
        if suffix:
            replace_expr = self.func(
                "REPLACE", cast_expr, exp.Literal.string(suffix), exp.Literal.string("")
            )
        else:
            replace_expr = cast_expr

        return TypedSelectExpression.from_sqlglot(
            replace_expr,
            DataType.STRING,
            arg.kind,
        )

    def supports_microseconds_in_timestamps(self) -> bool:
        """
        Returns whether the dialect supports fractional seconds in timestamps.
        """
        return True

    def clamp_left_right_to_str_length(self) -> bool:
        """
        Returns whether we should clamp the size argument to the left/right functions
        to never exceed the length of the string. Trino/Athena return an empty string
        in this case rather than including all of the characters.
        """
        return False

    def join_condition_matches_nulls(
        self, lhs: exp.Expression, rhs: exp.Expression
    ) -> exp.Expression:
        """
        Build the join ON condition that matches nulls.
        """

        # Wrap expressions in parentheses if needed for IS NULL checks
        # to ensure proper operator precedence (e.g., for concatenation)
        def maybe_paren(expr: exp.Expression) -> exp.Expression:
            if _needs_parens_for_substitution(expr):
                return exp.Paren(this=expr)
            return expr

        return exp.or_(
            exp.EQ(
                this=lhs,
                expression=rhs,
            ),
            exp.and_(
                exp.Is(this=maybe_paren(lhs), expression=exp.null()),
                exp.Is(this=maybe_paren(rhs), expression=exp.null()),
            ),
        )

    def concat(self, *args: TypedSelectExpression) -> TypedSelectExpression:
        """
        Build a CONCAT expression that treats NULLs as empty strings.

        This ensures consistent behavior across all dialects where NULLs are
        converted to empty strings in concat operations.
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

    def compile_literal(
        self,
        literal: Any,
        context: ExpressionContext | None = None,
        data_type: DataType | None = None,
    ) -> TypedSelectExpression:
        """
        Compile a literal value to the dialect's representation.

        Args:
            literal: The literal value to compile.
            context: The context of the expression. If None (the default), then
                     the literal is compiled as a scalar expression that's appropriate
                     for use in a nested expression. When provided, the context
                     indicates that the literal is a top-level expression used in the
                     provided context.
            data_type: Optional data type to use. If None, will be inferred.

        Returns:
            TypedSelectExpression: The compiled typed select expression.
        """

        def _compile_literal_inner(
            literal: Any,
            data_type: DataType | None,
        ) -> TypedSelectExpression:
            """Inner function that compiles literals without context wrapping."""
            # Handle None/NULL
            if literal is None:
                null_expr: exp.Expression = exp.Null()
                if (
                    data_type is not None
                    and self.null_literals_should_be_cast_to_type()
                ):
                    # Cast NULL to the specified type if dialect requires it
                    sqlglot_type = datatype_to_sqlglot(data_type)
                    null_expr = exp.Cast(
                        this=null_expr, to=exp.DataType.build(sqlglot_type)
                    )
                return TypedSelectExpression.from_sqlglot(
                    null_expr, data_type or DataType.NULL, ExpressionKind.SCALAR
                )

            # Handle boolean
            if isinstance(literal, bool):
                return TypedSelectExpression.from_sqlglot(
                    exp.Boolean(this=literal), DataType.BOOLEAN, ExpressionKind.SCALAR
                )

            # Handle numeric types
            if isinstance(literal, int):
                return TypedSelectExpression.from_sqlglot(
                    exp.Literal.number(literal), DataType.NUMBER, ExpressionKind.SCALAR
                )

            if isinstance(literal, float):
                if math.isnan(literal) or math.isinf(literal):
                    if not self.supports_non_finite_floats():
                        literal_expr: exp.Expression
                        if self.null_literals_should_be_cast_to_type():
                            literal_expr = exp.cast(
                                exp.null(), exp.DataType.Type.DOUBLE
                            )
                        else:
                            literal_expr = exp.null()
                        return TypedSelectExpression.from_sqlglot(
                            literal_expr,
                            data_type=DataType.NUMBER,
                        )
                    else:
                        # Create NaN or Infinity expression
                        if math.isnan(literal):
                            return TypedSelectExpression.from_sqlglot(
                                exp.Cast(
                                    this=exp.Literal.string("NaN"),
                                    to=exp.DataType.build("DOUBLE"),
                                ),
                                DataType.NUMBER,
                                ExpressionKind.SCALAR,
                            )
                        elif math.isinf(literal):
                            if literal > 0:
                                return self.cast_to_float(
                                    TypedSelectExpression.from_sqlglot(
                                        exp.Literal.string("Infinity"),
                                        DataType.NUMBER,
                                        ExpressionKind.SCALAR,
                                    )
                                )
                            else:
                                return self.cast_to_float(
                                    TypedSelectExpression.from_sqlglot(
                                        exp.Literal.string("-Infinity"),
                                        DataType.NUMBER,
                                        ExpressionKind.SCALAR,
                                    )
                                )
                else:
                    return TypedSelectExpression.from_sqlglot(
                        exp.Literal.number(literal),
                        DataType.NUMBER,
                        ExpressionKind.SCALAR,
                    )

            # Handle string
            if isinstance(literal, str):
                return TypedSelectExpression.from_sqlglot(
                    exp.Literal.string(literal), DataType.STRING, ExpressionKind.SCALAR
                )

            # Handle date objects

            if isinstance(literal, datetime.date) and not isinstance(
                literal, datetime.datetime
            ):
                # Convert date to string in ISO format
                date_str = literal.isoformat()
                # Use dialect-specific date literal syntax
                date_expr = exp.Cast(
                    this=exp.Literal.string(date_str), to=exp.DataType.build("DATE")
                )
                return TypedSelectExpression.from_sqlglot(
                    date_expr, DataType.DATE, ExpressionKind.SCALAR
                )

            # Handle datetime objects
            if isinstance(literal, datetime.datetime):
                # Check if datetime has timezone info
                if literal.tzinfo is not None:
                    # This is a timezone-aware datetime (TIMESTAMPTZ)
                    # Convert to ISO format with timezone
                    dt_str = literal.isoformat()
                    # Use dialect-specific timestamp with timezone literal syntax
                    ts_expr = exp.Cast(
                        this=exp.Literal.string(dt_str),
                        to=exp.DataType.build("TIMESTAMPTZ"),
                    )
                    return TypedSelectExpression.from_sqlglot(
                        ts_expr, DataType.TIMESTAMPTZ, ExpressionKind.SCALAR
                    )
                else:
                    # This is a naive datetime (TIMESTAMP)
                    # Convert datetime to string in ISO format with microseconds
                    # Use isoformat() to preserve microseconds if present
                    dt_str = literal.isoformat(sep=" ")
                    # Use dialect-specific timestamp literal syntax
                    ts_expr = exp.Cast(
                        this=exp.Literal.string(dt_str),
                        to=exp.DataType.build("TIMESTAMP"),
                    )
                    return TypedSelectExpression.from_sqlglot(
                        ts_expr, DataType.TIMESTAMP, ExpressionKind.SCALAR
                    )

            # For other types, try to convert to string
            return TypedSelectExpression.from_sqlglot(
                exp.Literal.string(str(literal)),
                data_type or DataType.STRING,
                ExpressionKind.SCALAR,
            )

        # Compile the literal using the inner function
        result = _compile_literal_inner(literal, data_type)

        # Apply context wrapping once if needed
        if context is not None:
            result = self.wrap_expression_for_context(result, context)

        return result

    def compile_expression(
        self,
        expr: CalcExpr,
        context: ExpressionContext,
        schema: Schema,
        timezone: str,
        parameters: Optional[dict[str, DataType]],
        substitutions: Optional[dict[str, TypedSelectExpression]] = None,
        wrap_for_context: bool = True,
        skip_mangle: Union[bool, list[str], None] = None,
    ) -> TypedSelectExpression:
        """
        Compile a Calc expression into a TypedSelectExpression within an
        expression context and schema.

        Args:
            expr: The Calc expression to compile.
            context: The context of the expression.
            schema: The schema context for the compilation.
                    If None, a schema with no columns is assumed.
            timezone: The local timezone to use for the compilation.
            parameters: A dictionary of parameter names to data types.
            substitutions: A dictionary of column names to expressions to substitute
                           for in the expression.
            wrap_for_context: Whether to wrap the resulting expression for the context.
            skip_mangle: Whether to skip mangling the column names. If a list of column
                         names is provided, then only the provided column names are
                         mangled. If True, then all column names are mangled.
                         If False or None, then column names are mangled according to
                         the dialect.

        Returns:
            TypedSelectExpression: The compiled typed select expression.
        """
        from hex_sl.calc.compiler import CalcToTypedSelectVisitor

        visitor = CalcToTypedSelectVisitor(
            self, context, schema, timezone, parameters, substitutions, skip_mangle
        )
        compiled: TypedSelectExpression = expr.root.accept(visitor)
        if wrap_for_context:
            compiled = self.wrap_expression_for_context(compiled, context)
        return compiled

    def resolve_hexsl_calc_placeholders(
        self,
        sqlglot_expr: exp.Expression,
        schema: Schema,
        timezone: str,
        context: ExpressionContext,
        parameters: Optional[dict[str, DataType]] = None,
        substitutions: Optional[dict[str, TypedSelectExpression]] = None,
    ) -> exp.Expression:
        """
        Resolve _hexsl_calc() placeholder functions by compiling the embedded
        calc expressions with full context.
        """
        from hex_sl.calc.ast.expr import CalcExpr
        from hex_sl.expr import _needs_parens_for_substitution

        def transform(node: exp.Expression) -> exp.Expression:
            from hex_sl.calc.visitor import _extract_hexsl_calc_string

            if calc_str := _extract_hexsl_calc_string(node):
                # Parse the calc expression from JSON
                calc_expr = CalcExpr.model_validate_json(calc_str)

                # Compile it with full context
                typed_expr = self.compile_expression(
                    calc_expr,
                    context=context,
                    schema=schema,
                    timezone=timezone,
                    parameters=parameters or {},
                    substitutions=substitutions or {},
                    wrap_for_context=False,
                )

                # Wrap in parens if needed
                result_expr = typed_expr.expression
                if _needs_parens_for_substitution(result_expr):
                    result_expr = exp.Paren(this=result_expr)

                return result_expr
            return node

        return sqlglot_expr.transform(transform)

    def wrap_expression_for_context(
        self, expr: TypedSelectExpression, context: ExpressionContext
    ) -> TypedSelectExpression:
        """
        Wrap a top-level expression for a given context.

        This is a no-op by default, and exists for the mssql dialect.
        """
        return expr

    def should_cast_dimension_type_by_default(self, dtype: DataType) -> bool:
        """
        Returns whether the dialect should cast a dimension types by default.

        This effectively sets the default value of the `cast` property of a
        dimension. This should not be considered if the `cast` property is
        set to True or False.

        Args:
            dtype: The data type of the dimension.

        Returns:
            bool: Whether the dialect should cast the dimension type by default.
        """
        return False

    def func(self, name: str, *args: Any) -> exp.Func:
        return exp.func(name, *args, dialect=self.sqlglot_dialect())

    # Expression building methods
    def build_null(self, data_type: DataType | None = None) -> TypedSelectExpression:
        """
        Build a NULL literal expression.

        Args:
            data_type: Optional data type to cast the NULL to

        Returns:
            A TypedSelectExpression representing NULL
        """
        return self.compile_literal(None, data_type=data_type)

    def build_ifelse(
        self,
        condition: TypedSelectExpression,
        then_expr: TypedSelectExpression,
        else_expr: TypedSelectExpression,
    ) -> TypedSelectExpression:
        """
        Build an IF/CASE WHEN conditional expression.

        Args:
            condition: The condition to test
            then_expr: Expression to return if condition is true
            else_expr: Expression to return if condition is false

        Returns:
            A TypedSelectExpression representing the conditional
        """
        # Delegate to build_case with a single condition
        return self.build_case(ifs=[(condition, then_expr)], default=else_expr)

    def build_case(
        self,
        ifs: list[tuple[TypedSelectExpression, TypedSelectExpression]],
        default: TypedSelectExpression | None = None,
    ) -> TypedSelectExpression:
        """
        Build a CASE statement with multiple conditions.

        Args:
            ifs: List of (condition, result) tuples
            default: Optional default expression if no conditions match

        Returns:
            A TypedSelectExpression representing the CASE statement
        """

        # Build list of IF expressions
        if_exprs = [
            exp.If(this=cond.expression, true=result.expression) for cond, result in ifs
        ]

        # Build CASE expression
        case_expr = exp.Case(
            ifs=if_exprs, default=default.expression if default else None
        )

        # Determine result type from all result branches
        result_types = [result.data_type for _, result in ifs]
        if default:
            result_types.append(default.data_type)
        result_type = self._common_type(*result_types)

        # Determine expression kind
        all_exprs = []
        for cond, result in ifs:
            all_exprs.extend([cond, result])
        if default:
            all_exprs.append(default)
        kind = ExpressionKind._validate_infer_kind([e.kind for e in all_exprs])

        return TypedSelectExpression.from_sqlglot(case_expr, result_type, kind)

    def build_coalesce(self, *args: TypedSelectExpression) -> TypedSelectExpression:
        """
        Build a COALESCE expression.

        Args:
            *args: Expressions to coalesce

        Returns:
            A TypedSelectExpression representing the COALESCE
        """

        if not args:
            msg = "COALESCE requires at least one argument"
            raise ValueError(msg)

        coalesce_expr = exp.Coalesce(
            this=args[0].expression, expressions=[arg.expression for arg in args[1:]]
        )

        # Determine result type
        result_type = self._common_type(*[arg.data_type for arg in args])

        # Determine expression kind
        kind = ExpressionKind._validate_infer_kind([arg.kind for arg in args])

        return TypedSelectExpression.from_sqlglot(coalesce_expr, result_type, kind)

    def build_greatest(self, *args: TypedSelectExpression) -> TypedSelectExpression:
        """
        Build a GREATEST expression.

        Args:
            *args: Expressions to find the greatest of

        Returns:
            A TypedSelectExpression representing the GREATEST
        """

        if not args:
            msg = "GREATEST requires at least one argument"
            raise ValueError(msg)

        greatest_expr = exp.Greatest(
            this=args[0].expression, expressions=[arg.expression for arg in args[1:]]
        )

        # Determine result type
        result_type = self._common_type(*[arg.data_type for arg in args])

        # Determine expression kind
        kind = ExpressionKind._validate_infer_kind([arg.kind for arg in args])

        return TypedSelectExpression.from_sqlglot(greatest_expr, result_type, kind)

    def build_least(self, *args: TypedSelectExpression) -> TypedSelectExpression:
        """
        Build a LEAST expression.

        Args:
            *args: Expressions to find the least of

        Returns:
            A TypedSelectExpression representing the LEAST
        """

        if not args:
            msg = "LEAST requires at least one argument"
            raise ValueError(msg)

        least_expr = exp.Least(
            this=args[0].expression, expressions=[arg.expression for arg in args[1:]]
        )

        # Determine result type
        result_type = self._common_type(*[arg.data_type for arg in args])

        # Determine expression kind
        kind = ExpressionKind._validate_infer_kind([arg.kind for arg in args])

        return TypedSelectExpression.from_sqlglot(least_expr, result_type, kind)

    def build_isnull(self, arg: TypedSelectExpression) -> TypedSelectExpression:
        """
        Build an IS NULL predicate.

        Args:
            arg: Expression to test for NULL

        Returns:
            A TypedSelectExpression representing the IS NULL test
        """

        is_null_expr = exp.Is(this=arg.expression, expression=exp.Null())

        return TypedSelectExpression.from_sqlglot(
            is_null_expr, DataType.BOOLEAN, arg.kind
        )

    def build_isnan(self, arg: TypedSelectExpression) -> TypedSelectExpression:
        """
        Build an IS NAN check.

        Args:
            arg: Expression to test for NaN

        Returns:
            A TypedSelectExpression representing the IS NAN test
        """

        if not self.supports_non_finite_floats():
            # Return false for dialects that don't support NaN
            return self.compile_literal(False)

        # Standard SQL: arg != arg (NaN is not equal to itself)
        isnan_expr = exp.NEQ(this=arg.expression, expression=arg.expression)

        return TypedSelectExpression.from_sqlglot(
            isnan_expr, DataType.BOOLEAN, arg.kind
        )

    def build_isinf(self, arg: TypedSelectExpression) -> TypedSelectExpression:
        """
        Build an IS INFINITE check.

        Args:
            arg: Expression to test for infinity

        Returns:
            A TypedSelectExpression representing the IS INFINITE test
        """

        if not self.supports_non_finite_floats():
            # Return false for dialects that don't support infinity
            return self.compile_literal(False)

        # Check if arg = 'Infinity' OR arg = '-Infinity'
        pos_inf = exp.Cast(
            this=exp.Literal.string("Infinity"), to=exp.DataType.build("DOUBLE")
        )
        neg_inf = exp.Cast(
            this=exp.Literal.string("-Infinity"), to=exp.DataType.build("DOUBLE")
        )

        isinf_expr = exp.Or(
            this=exp.EQ(this=arg.expression, expression=pos_inf),
            expression=exp.EQ(this=arg.expression, expression=neg_inf),
        )

        return TypedSelectExpression.from_sqlglot(
            isinf_expr, DataType.BOOLEAN, arg.kind
        )

    def build_round(self, arg: TypedSelectExpression) -> TypedSelectExpression:
        """
        Build a ROUND expression to round to the nearest integer.

        Args:
            arg: Expression to round

        Returns:
            A TypedSelectExpression representing the ROUND operation
        """

        # Default implementation uses single-argument ROUND
        round_expr = exp.Round(this=arg.expression)

        return TypedSelectExpression.from_sqlglot(round_expr, DataType.NUMBER, arg.kind)

    def build_median(self, arg: TypedSelectExpression) -> TypedSelectExpression:
        """
        Build a MEDIAN expression.

        Args:
            arg: Expression to compute median of

        Returns:
            A TypedSelectExpression representing the MEDIAN operation
        """

        # Default implementation uses native MEDIAN function
        # Cast to float using dialect method
        cast_typed = self.cast_to_float(arg)

        # Use native MEDIAN function
        median_expr = self.func("MEDIAN", cast_typed.expression)

        return TypedSelectExpression.from_sqlglot(
            median_expr, DataType.NUMBER, arg.kind
        )

    def build_division(
        self, left: TypedSelectExpression, right: TypedSelectExpression
    ) -> TypedSelectExpression:
        """
        Build a division expression.

        Args:
            left: The dividend
            right: The divisor

        Returns:
            A TypedSelectExpression representing the division
        """

        # Wrap left operand in parentheses if it's a binary op with lower precedence
        # This handles cases like (a - b) / c vs a - b / c
        left_expr = left.expression
        if isinstance(left_expr, (exp.Add, exp.Sub)):
            left_expr = exp.Paren(this=left_expr)

        div_expr = exp.Div(this=left_expr, expression=right.expression)

        # Determine expression kind
        kind = ExpressionKind._validate_infer_kind([left.kind, right.kind])

        # For numeric division, result is NUMBER
        return TypedSelectExpression.from_sqlglot(div_expr, DataType.NUMBER, kind)

    def build_interval(
        self,
        count: int,
        unit: Literal[
            "day", "hour", "minute", "second", "millisecond", "month", "year"
        ],
    ) -> TypedSelectExpression:
        """
        Build a time interval expression.

        Args:
            count: The number of units
            unit: The time unit

        Returns:
            A TypedSelectExpression representing the interval
        """

        # Map unit names to sqlglot interval units
        unit_map = {
            "day": "DAY",
            "hour": "HOUR",
            "minute": "MINUTE",
            "second": "SECOND",
            "millisecond": "MILLISECOND",
            "month": "MONTH",
            "year": "YEAR",
        }

        interval_expr = exp.Interval(  # type: ignore[no-untyped-call]
            this=exp.Literal.number(count), unit=unit_map.get(unit, unit.upper())
        )

        # Intervals are typically treated as a special duration type
        # For now, we'll use STRING as the data type
        return TypedSelectExpression.from_sqlglot(
            interval_expr, DataType.STRING, ExpressionKind.SCALAR
        )

    # Helper methods for type inference
    def _common_type(self, *types: DataType) -> DataType:
        """Determine the common type among multiple data types."""
        # Filter out NULL types
        non_null_types = [t for t in types if t != DataType.NULL]

        if not non_null_types:
            return DataType.NULL

        # If all types are the same, return that type
        if all(t == non_null_types[0] for t in non_null_types):
            return non_null_types[0]

        # Type promotion rules
        # If any type is STRING, promote to STRING
        if any(t == DataType.STRING for t in non_null_types):
            return DataType.STRING

        # If mix of numeric types, promote to NUMBER
        numeric_types = {DataType.NUMBER}
        if all(t in numeric_types for t in non_null_types):
            return DataType.NUMBER

        # If mix of date/timestamp types, promote to TIMESTAMPTZ
        temporal_types = {DataType.DATE, DataType.TIMESTAMP, DataType.TIMESTAMPTZ}
        if all(t in temporal_types for t in non_null_types):
            return DataType.TIMESTAMPTZ

        # Default to first non-null type
        return non_null_types[0]

    # List of canonical dialect names
    all_dialects: ClassVar[list[str]] = [
        "bigquery",
        "clickhouse",
        "duckdb",
        "mssql",
        "mysql",
        "postgres",
        "redshift",
        "snowflake",
        "spark",
        "trino",
    ]

    @classmethod
    def from_name(cls, name: str) -> Dialect:
        """
        Returns the dialect from the name.

        Args:
            name: Dialect name (case-insensitive). Accepts both canonical names
                  (e.g., "trino", "postgres") and aliases (e.g., "athena", "alloydb").

        Returns:
            Dialect: The dialect instance.

        Raises:
            ValueError: If the dialect name is not supported.
        """
        # Use shared normalization function to validate and resolve aliases
        canonical_name = normalize_dialect_name(name)

        if canonical_name == "trino":
            from hex_sl_utils.dialect.trino import Trino

            return Trino()
        elif canonical_name == "bigquery":
            from hex_sl_utils.dialect.bigquery import BigQuery

            return BigQuery()
        elif canonical_name == "clickhouse":
            from hex_sl_utils.dialect.clickhouse import ClickHouse

            return ClickHouse()
        elif canonical_name == "spark":
            from hex_sl_utils.dialect.spark import Spark

            return Spark()
        elif canonical_name in ("duckdb", "motherduck"):
            from hex_sl_utils.dialect.duckdb import DuckDB

            return DuckDB()
        elif canonical_name == "mssql":
            from hex_sl_utils.dialect.mssql import MSSQL

            return MSSQL()
        elif canonical_name == "mysql":
            from hex_sl_utils.dialect.mysql import MySQL

            return MySQL()
        elif canonical_name == "postgres":
            from hex_sl_utils.dialect.postgres import Postgres

            return Postgres()
        elif canonical_name == "redshift":
            from hex_sl_utils.dialect.redshift import Redshift

            return Redshift()
        elif canonical_name == "snowflake":
            from hex_sl_utils.dialect.snowflake import Snowflake

            return Snowflake()
        else:
            # This should not be reached as normalize_dialect_name validates
            msg = f"Unsupported dialect: {name}"
            raise ValueError(msg)
