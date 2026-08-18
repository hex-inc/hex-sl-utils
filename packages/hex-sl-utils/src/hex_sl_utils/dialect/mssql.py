from __future__ import annotations

import datetime
from typing import Any, ClassVar

from hex_sl_utils._vendor.sqlglot import exp, tokens, transforms
from hex_sl_utils._vendor.sqlglot.dialects.dialect import rename_func
from hex_sl_utils._vendor.sqlglot.dialects.tsql import TSQL
from hex_sl_utils._vendor.sqlglot.helper import flatten, seq_get
from hex_sl_utils._vendor.sqlglot.tokens import TokenType
from hex_sl_utils.datatype import DataType
from hex_sl_utils.dialect.dialect import Dialect
from hex_sl_utils.dialect.dialect_name import DialectName
from hex_sl_utils.dialect.mssql_utils import extract_static_sqlglot_constant
from hex_sl_utils.dialect.placeholder import (
    PlaceholderGeneratorMixin,
    parse_jinja_placeholder,
    placeholder_parser_mapping,
    placeholder_sql,
)
from hex_sl_utils.dialect.transforms import hex_sl_eliminate_qualify
from hex_sl_utils.exception import UnsupportedByDialectError
from hex_sl_utils.expr import ExpressionContext, ExpressionKind, TypedSelectExpression
from hex_sl_utils.time import TimeTruncUnit
from hex_sl_utils.timezone import iana_to_windows


class MSSQL(Dialect):
    @classmethod
    def name(cls) -> DialectName:
        return "mssql"

    @classmethod
    def sqlglot_dialect(cls) -> str:
        return "hex-sl-mssql"

    def supports_groupby_by_index(self) -> bool:
        return False

    def truncates_on_integer_division(self) -> bool:
        return True

    def mod_supports_floats(self) -> bool:
        return True

    def supports_median(self) -> bool:
        return False

    def supports_non_finite_floats(self) -> bool:
        return False

    def supports_cot_function(self) -> bool:
        return False

    def build_round(self, arg: TypedSelectExpression) -> TypedSelectExpression:
        """
        Build a ROUND expression for MSSQL.

        MSSQL requires a precision argument for the ROUND function.
        For rounding to the nearest integer, we use precision 0.
        """

        # MSSQL ROUND(number, precision) - use 0 for rounding to nearest integer
        round_expr = self.func("ROUND", arg.expression, exp.Literal.number(0))

        return TypedSelectExpression.from_sqlglot(round_expr, DataType.NUMBER, arg.kind)

    def use_empty_over_for_count_star_window_function(self) -> bool:
        return True

    def supports_window_partition_by_alias(self) -> bool:
        """
        MSSQL does not allow using column aliases in PARTITION BY clauses of window
        functions. Must use original expressions.
        """
        return False

    def supports_inequality_joins(self) -> bool:
        """
        MSSQL technically supports inequality joins, but performs extremely poorly
        on the range joins required for rolling/cumulative measures.
        """
        return False

    def wrap_expression_for_context(
        self, expr: TypedSelectExpression, context: ExpressionContext
    ) -> TypedSelectExpression:
        """
        Wrap a top-level expression for a given context

        MSSQL is unique in its handling of boolean expressions. MSSQL supports
        boolean operators, like 1 < 2, but the result of these cannot be used
        as a top-level expression. MSSQL has no boolean column type. Instead,
        boolean expressions are only valid in certain contexts. In particular,
        they are valid in the WHERE clause, and in CASE statements, and as the
        first argument to the IIF function.

        Any time we encounter a boolean expression as a top-level expression,
        we wrap it in an IIF function to convert false to 0 and true to 1.
        This can only be done at the top-level, because we can't convert a boolean
        expression to 0 and 1 if it's nested inside a valid expression like a CASE
        statement.

        Furthermore, these integer values cannot be used in a context that expects
        a boolean expression. so `SELECT * FROM foo WHERE IIF(1 = 2, true, false)`
        is invalid. To address these constraints, we need to apply the following
        rules:
         1. If a boolean expression is used as a top-level expression in a
            PROJECTION or AGGREGATION context, we convert it to an integer by
            wrapping it in an IIF function. Select functions and operators may
            opt-in to treating their arguments as top-level if they can handle
            accepting boolean values as integers.
         2. If an integer expression is used as a top-level expression in a
            WHERE or HAVING context, we convert it to a boolean expression by
            checking whether it is not equal to 0.
        """

        # mssql doesn't have a boolean type, so boolean expressions need to be
        # replaced by ints. The cast to boolean converts the int to the most
        # appropriate approximation
        if (
            context in (ExpressionContext.PROJECTION, ExpressionContext.AGGREGATION)
            and expr.data_type == DataType.BOOLEAN
        ):
            sg_expr: exp.Expression = exp.If(
                this=expr.expression,
                true=exp.Literal.number(1),
                false=exp.Literal.number(0),
            )
            return TypedSelectExpression.from_sqlglot(sg_expr, DataType.NUMBER)
        elif (
            context in (ExpressionContext.WHERE, ExpressionContext.HAVING)
            and expr.data_type == DataType.NUMBER
        ):
            sg_expr = exp.NEQ(this=expr.expression, expression=exp.Literal.number(0))
            return TypedSelectExpression.from_sqlglot(sg_expr, DataType.BOOLEAN)

        return expr

    def compile_literal(
        self,
        literal: Any,
        context: ExpressionContext | None = None,
        data_type: DataType | None = None,
    ) -> TypedSelectExpression:
        """
        Compile a literal expression with MSSQL-specific date and datetime handling.

        MSSQL uses DATEFROMPARTS(year, month, day) for date literals and
        DATETIMEOFFSETFROMPARTS/DATETIME2FROMPARTS for datetime literals.
        """

        # Handle boolean literals with PROJECTION context - compile directly to 1 or 0
        if isinstance(literal, bool) and context == ExpressionContext.PROJECTION:
            result = TypedSelectExpression.from_sqlglot(
                exp.Literal.number(1 if literal else 0),
                DataType.NUMBER,
                ExpressionKind.SCALAR,
            )
            return result

        # Handle datetime objects with MSSQL-specific FROMPARTS functions
        elif isinstance(literal, datetime.datetime):
            # Extract datetime components
            year = literal.year
            month = literal.month
            day = literal.day
            hour = literal.hour
            minute = literal.minute
            second = literal.second
            # MSSQL uses fractional seconds (microseconds as int, precision=6)
            fractions = literal.microsecond

            if literal.tzinfo is not None:
                # This is a timezone-aware datetime (TIMESTAMPTZ)
                # Use DATETIMEOFFSETFROMPARTS(year, month, day, hour, minute,
                # seconds, fractions, hour_offset, minute_offset, precision)
                # For UTC timezone, hour_offset=0, minute_offset=0
                ts_expr = self.func(
                    "DATETIMEOFFSETFROMPARTS",
                    exp.Literal.number(year),
                    exp.Literal.number(month),
                    exp.Literal.number(day),
                    exp.Literal.number(hour),
                    exp.Literal.number(minute),
                    exp.Literal.number(second),
                    exp.Literal.number(fractions),
                    exp.Literal.number(0),  # hour_offset for UTC
                    exp.Literal.number(0),  # minute_offset for UTC
                    exp.Literal.number(6),  # precision (microseconds)
                )
                result = TypedSelectExpression.from_sqlglot(
                    ts_expr, DataType.TIMESTAMPTZ, ExpressionKind.SCALAR
                )
            else:
                # This is a naive datetime (TIMESTAMP)
                # Use DATETIME2FROMPARTS(year, month, day, hour, minute,
                # seconds, fractions, precision)
                ts_expr = self.func(
                    "DATETIME2FROMPARTS",
                    exp.Literal.number(year),
                    exp.Literal.number(month),
                    exp.Literal.number(day),
                    exp.Literal.number(hour),
                    exp.Literal.number(minute),
                    exp.Literal.number(second),
                    exp.Literal.number(fractions),
                    exp.Literal.number(6),  # precision (microseconds)
                )
                result = TypedSelectExpression.from_sqlglot(
                    ts_expr, DataType.TIMESTAMP, ExpressionKind.SCALAR
                )

            if context is not None:
                result = self.wrap_expression_for_context(result, context)
            return result
        # Handle date objects with MSSQL-specific DATEFROMPARTS function
        elif isinstance(literal, datetime.date) and not isinstance(
            literal, datetime.datetime
        ):
            # Use DATEFROMPARTS(year, month, day) for MSSQL
            date_expr = self.func(
                "DATEFROMPARTS",
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
        self,
        arg: TypedSelectExpression,
    ) -> TypedSelectExpression:
        naive_seconds_ts = exp.Anonymous(
            this="DATEADD",
            expressions=[
                "s",
                exp.Div(this=arg.expression, expression=exp.Literal.number(1_000)),
                exp.Literal.string("1970-01-01 00:00:00"),
            ],
        )

        # Use microseconds instead of milliseconds to avoid rounding errors
        micros_part = exp.Mul(
            this=exp.paren(
                exp.Mod(
                    this=exp.paren(arg.expression), expression=exp.Literal.number(1000)
                )
            ),
            expression=exp.Literal.number(1000),
        )

        naive_ts = TypedSelectExpression.from_sqlglot(
            exp.DateAdd(  # type: ignore[no-untyped-call]
                this=exp.cast(naive_seconds_ts, to=exp.DataType.Type.TIMESTAMP),
                unit=exp.Literal.string("microsecond"),
                expression=micros_part,
            ),
            DataType.TIMESTAMPTZ,
            kind=arg.kind,
        )

        return self.at_timezone(naive_ts, "UTC")

    def datetime_to_epoch_ms(self, arg: TypedSelectExpression) -> TypedSelectExpression:
        if arg.data_type == DataType.TIMESTAMPTZ:
            # Always convert to UTC before extracting epoch millis
            arg = self.at_timezone(arg, "UTC")

        datetime2 = exp.DataType.build("DATETIME2", dialect=self.sqlglot_dialect())
        result: exp.Expression = exp.Mul(
            this=exp.Cast(
                this=self.func(
                    "DATEDIFF",
                    exp.Var(this="S"),
                    exp.Cast(
                        this=exp.Literal.string("1970-01-01 00:00:00"),
                        to=datetime2,
                    ),
                    exp.Cast(
                        this=arg.expression,
                        to=datetime2,
                    ),
                ),
                to=exp.DataType.build("BIGINT"),
            ),
            expression=exp.Literal.number(1_000),
        )
        if arg.data_type != DataType.DATE:
            # add back the milliseconds if possible
            result = exp.Add(
                this=exp.Paren(this=result),
                expression=self.func(
                    "DATEPART",
                    exp.Identifier(this="millisecond"),
                    arg.expression,
                ),
            )
            # Wrap the entire expression in parentheses to ensure proper
            # precedence in arithmetic operations
            result = exp.Paren(this=result)

        return TypedSelectExpression.from_sqlglot(result, DataType.NUMBER)

    def day_of_week_part(
        self,
        arg: TypedSelectExpression,
        timezone: str,
    ) -> TypedSelectExpression:
        if arg.data_type == DataType.TIMESTAMPTZ:
            arg = self.at_timezone(arg, timezone)

        # Ibis has this off by one compared to its usual standard.
        # MSSQL already uses Sunday = 1 and Saturday = 7, which is what
        # we need
        return TypedSelectExpression.from_sqlglot(
            self.func(
                "DATEPART", exp.to_identifier("DW", quoted=False), arg.expression
            ),
            DataType.NUMBER,
            kind=arg.kind,
        )

    def datetime_trunc(
        self,
        arg: TypedSelectExpression,
        unit: TimeTruncUnit,
        tz: str,
    ) -> TypedSelectExpression:
        # SQL Server 2022 supports DATE_TRUNC, but 2018 does not.
        # Our current minimum version is 2018, but this can be simplified if
        # we raise that to 2022 in the future.

        convert_tz = (
            iana_to_windows(tz)
            if tz and arg.data_type == DataType.TIMESTAMPTZ
            else None
        )

        # Apply timezone if provided, otherwise use the original expression
        tz_expression = (
            exp.AtTimeZone(this=arg.expression, zone=exp.Literal.string(convert_tz))
            if convert_tz is not None
            else arg.expression
        )

        millis_part = self.func(
            "DATEPART", exp.to_identifier("millisecond"), tz_expression
        )
        seconds_part = self.func("DATEPART", exp.to_identifier("second"), tz_expression)
        minutes_part = self.func("DATEPART", exp.to_identifier("minute"), tz_expression)
        hours_part = self.func("DATEPART", exp.to_identifier("hour"), tz_expression)
        days_part = self.func("DATEPART", exp.to_identifier("day"), tz_expression)
        months_part = self.func("DATEPART", exp.to_identifier("month"), tz_expression)
        years_part = self.func("DATEPART", exp.to_identifier("year"), tz_expression)
        day_of_week_part = self.func(
            "DATEPART", exp.to_identifier("weekday"), tz_expression
        )

        one = exp.Literal.number(1)
        zero = exp.Literal.number(0)
        five = exp.Literal.number(5)
        seven = exp.Literal.number(7)

        expression: exp.Expression
        if unit == "year":
            expression = self.func(
                "DATETIME2FROMPARTS", years_part, one, one, zero, zero, zero, zero, 3
            )
        elif unit == "quarter":
            expression = self.func(
                "DATETIME2FROMPARTS",
                years_part,
                exp.Add(
                    this=exp.Mul(
                        this=exp.Floor(
                            this=exp.Div(
                                this=exp.paren(
                                    exp.Sub(this=months_part, expression=one)
                                ),
                                expression=exp.Literal.number(3),
                            )
                        ),
                        expression=exp.Literal.number(3),
                    ),
                    expression=one,
                ),
                one,
                zero,
                zero,
                zero,
                zero,
                3,
            )
        elif unit == "month":
            expression = self.func(
                "DATETIME2FROMPARTS",
                years_part,
                months_part,
                one,
                zero,
                zero,
                zero,
                zero,
                3,
            )
        elif unit == "week":
            day_expression = self.func(
                "DATETIME2FROMPARTS",
                years_part,
                months_part,
                days_part,
                zero,
                zero,
                zero,
                zero,
                3,
            )
            expression = exp.DateAdd(  # type: ignore[no-untyped-call]
                this=day_expression,
                unit=exp.Literal.string("day"),
                expression=exp.Add(this=exp.Neg(this=day_of_week_part), expression=one),
            )
        elif unit == "weekmonday":
            day_expression = self.func(
                "DATETIME2FROMPARTS",
                years_part,
                months_part,
                days_part,
                zero,
                zero,
                zero,
                zero,
                3,
            )
            expression = exp.DateAdd(  # type: ignore[no-untyped-call]
                this=day_expression,
                unit=exp.Literal.string("day"),
                expression=exp.Add(
                    this=exp.Neg(
                        this=exp.paren(
                            exp.Add(
                                this=exp.paren(
                                    exp.Mod(
                                        this=exp.paren(
                                            exp.Add(
                                                this=day_of_week_part, expression=five
                                            )
                                        ),
                                        expression=seven,
                                    )
                                ),
                                expression=one,
                            )
                        )
                    ),
                    expression=one,
                ),
            )

        elif unit == "day":
            expression = self.func(
                "DATETIME2FROMPARTS",
                years_part,
                months_part,
                days_part,
                zero,
                zero,
                zero,
                zero,
                3,
            )
        elif unit == "hour":
            expression = self.func(
                "DATETIME2FROMPARTS",
                years_part,
                months_part,
                days_part,
                hours_part,
                zero,
                zero,
                zero,
                3,
            )
        elif unit == "minute":
            expression = self.func(
                "DATETIME2FROMPARTS",
                years_part,
                months_part,
                days_part,
                hours_part,
                minutes_part,
                zero,
                zero,
                3,
            )
        elif unit == "second":
            expression = self.func(
                "DATETIME2FROMPARTS",
                years_part,
                months_part,
                days_part,
                hours_part,
                minutes_part,
                seconds_part,
                zero,
                3,
            )
        elif unit == "millisecond":
            expression = self.func(
                "DATETIME2FROMPARTS",
                years_part,
                months_part,
                days_part,
                hours_part,
                minutes_part,
                seconds_part,
                millis_part,
                3,
            )

        if arg.data_type == DataType.DATE:
            expression = exp.Cast(this=expression, to=exp.DataType.build("DATE"))
        else:
            if convert_tz is not None:
                expression = exp.AtTimeZone(
                    this=expression, zone=exp.Literal.string(convert_tz)
                )

        return TypedSelectExpression.from_sqlglot(
            expression, arg.data_type, kind=arg.kind
        )

    def at_timezone(self, arg: TypedSelectExpression, tz: str) -> TypedSelectExpression:
        windows_tz = iana_to_windows(tz)
        # SQL Server's AT TIME ZONE always returns a datetimeoffset
        # (timestamp with time zone)
        return TypedSelectExpression.from_sqlglot(
            exp.AtTimeZone(this=arg.expression, zone=exp.Literal.string(windows_tz)),
            DataType.TIMESTAMPTZ,
            kind=arg.kind,
        )

    def startswith(
        self, string: TypedSelectExpression, prefix: TypedSelectExpression
    ) -> TypedSelectExpression:
        """
        Build expression to check if a string starts with a substring.

        MSSQL implementation uses LEFT(string, LEN(prefix)) = prefix.
        wrap_expression_for_context will handle IIF wrapping when needed.
        """

        eq_expr = exp.EQ(
            this=self.func(
                "LEFT", string.expression, self.func("LEN", prefix.expression)
            ),
            expression=prefix.expression,
        )

        return TypedSelectExpression.from_sqlglot(
            eq_expr,
            DataType.BOOLEAN,
            kind=ExpressionKind._validate_infer_kind([string.kind, prefix.kind]),
        )

    def endswith(
        self, string: TypedSelectExpression, suffix: TypedSelectExpression
    ) -> TypedSelectExpression:
        """
        Build expression to check if a string ends with a substring.

        MSSQL implementation uses RIGHT(string, LEN(suffix)) = suffix.
        wrap_expression_for_context will handle IIF wrapping when needed.
        """

        eq_expr = exp.EQ(
            this=self.func(
                "RIGHT", string.expression, self.func("LEN", suffix.expression)
            ),
            expression=suffix.expression,
        )

        return TypedSelectExpression.from_sqlglot(
            eq_expr,
            DataType.BOOLEAN,
            kind=ExpressionKind._validate_infer_kind([string.kind, suffix.kind]),
        )

    def today(self, timezone: str) -> TypedSelectExpression:
        return TypedSelectExpression.from_sqlglot(
            exp.Cast(this=exp.CurrentDate(), to=exp.DataType.build("DATE")),
            DataType.DATE,
            kind=ExpressionKind.SCALAR,
        )

    def timestamp_subsecond_suffix(self) -> str | None:
        # MSSQL uses 6 decimal places for DATETIME2
        return ".000000"

    def splitpart(
        self,
        string: TypedSelectExpression,
        delimiter: TypedSelectExpression,
        part_number: TypedSelectExpression,
    ) -> TypedSelectExpression:
        """
        MSSQL does not have a built-in SPLIT function, nor does it have a
        good replacement for it...

        The good news is that in the vast majority of cases, the part number
        is a small integer constant. So we can support up to some value N by
        repeatedly nesting CHARINDEX calls with compounding offsets.

        We could maybe support arbitrary part numbers, but the best we could
        do is create a correlated subquery with `SPLIT_STRING` and then extract
        the nth matching value, but this is not supported until SQL Server 2022:
        https://learn.microsoft.com/en-us/sql/t-sql/functions/string-split-transact-sql?view=sql-server-ver16#enable_ordinal
        Would be a (potentially correlated) subquery like:
            SELECT value FROM STRING_SPLIT(string, delimiter, 1)
            WHERE ordinal = part_number
        That would be potentially correct, but slow, so if we decide to raise
        the minimum version to 2022, we would still only fall back to this past
        the N manually enumerated cases.
        """

        # LEN does not include space characters, so we need to use DATALENGTH
        delimiter_length = exp.Anonymous(
            this="DATALENGTH", expressions=[delimiter.expression]
        )

        def safe_charindex(
            delimiter: exp.Expression,
            search: exp.Expression,
            start_pos: exp.Expression | None = None,
        ) -> exp.Expression:
            safe_searchable = exp.Collate(
                # SQL Server can fail if there was no match from a `CHARINDEX` call,
                # so we use concat it to the end so there's always a valid index.
                this=exp.Concat(expressions=[search, delimiter]),
                # specify a binary collation to force an exact match
                expression="Latin1_General_BIN2",
            )
            return exp.Anonymous(
                this="CHARINDEX",
                expressions=(
                    [delimiter, safe_searchable]
                    if not start_pos
                    else [delimiter, safe_searchable, start_pos]
                ),
            )

        def charindex_n(n: int) -> exp.Expression:
            """Return the index of the nth instance of the delimiter in the string."""
            # Base call: CHARINDEX(delimiter, str_col + delimiter)
            # We append delimiter to handle edge cases (like last part)
            expr = safe_charindex(
                delimiter.expression,
                string.expression,
            )
            # For k > 1, nest CHARINDEX calls as end position of prior
            for _ in range(1, n):
                expr = safe_charindex(
                    delimiter.expression,
                    string.expression,
                    expr + delimiter_length,
                )
            return expr

        def substring_n(n: int) -> exp.Expression:
            """Gets the nth substring of the string, split on the delimiter."""
            if n == 1:
                # special handling for n=1, which can be handled by a simple LEFT
                return exp.Left(
                    this=string.expression,
                    expression=safe_charindex(
                        delimiter.expression,
                        string.expression,
                    )
                    - 1,
                )
            # else:
            start_pos = (
                safe_charindex(
                    delimiter.expression,
                    string.expression,
                    charindex_n(n - 1),
                )
                + delimiter_length
            )
            end_pos = charindex_n(n)
            length = end_pos - start_pos
            return exp.If(
                # guard against out of bounds cases
                this=exp.LT(this=length, expression=self.compile_literal(0).expression),
                true=self.compile_literal("").expression,
                false=exp.Anonymous(
                    this="SUBSTRING", expressions=[string.expression, start_pos, length]
                ),
            )

        # by default, we support part numbers 1 to some fixed N, however, if we
        # detect that the part number is a statically provided constant, we can
        # save some SQL by just compiling that one case.
        max_dynamic_part_number = 5
        max_constant_part_number = 15
        [is_constant_part_number, constant_part_number] = (
            extract_static_sqlglot_constant(part_number.expression)
        )
        if is_constant_part_number and constant_part_number > max_constant_part_number:
            msg = f"Part number {constant_part_number} is too large"
            raise UnsupportedByDialectError(msg)
        if is_constant_part_number:
            result_expr = substring_n(constant_part_number)
        else:
            result_expr = exp.Case()
            for n in range(1, max_dynamic_part_number + 1):
                result_expr = result_expr.when(
                    exp.EQ(
                        this=part_number.expression,
                        expression=self.compile_literal(n).expression,
                    ),
                    substring_n(n),
                )
            result_expr = result_expr.else_(exp.Null())

        # prep and return
        kind = ExpressionKind._validate_infer_kind(
            [
                string.kind,
                delimiter.kind,
                part_number.kind,
            ]
        )
        return TypedSelectExpression.from_sqlglot(
            result_expr,
            DataType.STRING,
            kind,
        )

    def str_length(self, string: TypedSelectExpression) -> TypedSelectExpression:
        """
        Build expression to get the length of a string.

        MSSQL's LEN function doesn't count trailing/leading whitespace, so we use
        LEN(CONCAT('A', string, 'Z')) - 2 to get the true length including whitespace.
        """

        kind = string.kind

        # Use CONCAT to wrap the string with 'A' and 'Z', then subtract 2
        concat_expr = exp.Concat(
            expressions=[
                exp.Literal.string("A"),
                string.expression,
                exp.Literal.string("Z"),
            ]
        )

        len_expr = self.func("LEN", concat_expr)
        length_expr = exp.Sub(this=len_expr, expression=exp.Literal.number(2))

        return TypedSelectExpression.from_sqlglot(length_expr, DataType.NUMBER, kind)

    def cast_to_string(self, arg: TypedSelectExpression) -> TypedSelectExpression:
        """
        Cast expression to string type for MSSQL.

        MSSQL requires VARCHAR(MAX) for large string values, otherwise VARCHAR
        defaults to a very small size (typically 30 characters).
        """

        cast_expr = exp.Cast(this=arg.expression, to=exp.DataType.build("VARCHAR(MAX)"))
        return TypedSelectExpression.from_sqlglot(cast_expr, DataType.STRING, arg.kind)

    def contains(
        self, string: TypedSelectExpression, substring: TypedSelectExpression
    ) -> TypedSelectExpression:
        """
        Build expression to check if a string contains a substring using CHARINDEX.
        wrap_expression_for_context will handle IIF wrapping when needed.
        """

        kind = ExpressionKind._validate_infer_kind([string.kind, substring.kind])

        # Use CHARINDEX(substring, string) > 0
        charindex_expr = self.func("CHARINDEX", substring.expression, string.expression)
        contains_expr = exp.GT(this=charindex_expr, expression=exp.Literal.number(0))

        return TypedSelectExpression.from_sqlglot(contains_expr, DataType.BOOLEAN, kind)

    def concat(self, *args: TypedSelectExpression) -> TypedSelectExpression:
        """
        Build a CONCAT expression for MSSQL.

        MSSQL's CONCAT function automatically skips NULL values in multi-argument
        calls and converts single NULL arguments to empty strings
        (by wrapping in COALESCE).
        """

        if len(args) == 0:
            return self.compile_literal("")
        elif len(args) == 1:
            # For single argument, wrap in COALESCE to handle NULL->empty string
            # conversion MSSQL's CONCAT(NULL) returns NULL, so we need this for
            # consistency
            return TypedSelectExpression.from_sqlglot(
                exp.Coalesce(
                    this=args[0].expression, expressions=[exp.Literal.string("")]
                ),
                DataType.STRING,
                args[0].kind,
            )
        else:
            # Use simple CONCAT without COALESCE wrapping for multi-arg
            # MSSQL handles NULLs gracefully for multi-argument cases
            kind = ExpressionKind._validate_infer_kind([arg.kind for arg in args])
            concat_expr = exp.Concat(expressions=[arg.expression for arg in args])
            return TypedSelectExpression.from_sqlglot(
                concat_expr, DataType.STRING, kind
            )


def _build_datepart(args: list[exp.Expression]) -> exp.Anonymous:
    return exp.Anonymous(
        this="DATEPART",
        expressions=[
            seq_get(args, 0),
            seq_get(args, 1),
        ],
    )


def _greatest(gen: TSQL.Generator, expression: exp.Expression) -> str:
    args = list(flatten(expression.args.values()))
    arg0 = seq_get(args, 0)
    arg1 = seq_get(args, 1)
    return gen.func("IIF", exp.GTE(this=arg0, expression=arg1), arg0, arg1)


def _least(gen: TSQL.Generator, expression: exp.Expression) -> str:
    args = list(flatten(expression.args.values()))
    arg0 = seq_get(args, 0)
    arg1 = seq_get(args, 1)
    return gen.func("IIF", exp.LTE(this=arg0, expression=arg1), arg0, arg1)


class MSSQLSqlGlotOverride(TSQL):
    @classmethod
    def dialect_name(cls) -> str:
        return "hex-sl-mssql"

    class Generator(PlaceholderGeneratorMixin, TSQL.Generator):
        def placeholder_sql(self, expression: exp.Placeholder) -> str:
            return placeholder_sql(self, expression)

        TRANSFORMS = TSQL.Generator.TRANSFORMS.copy() | {
            exp.ApproxDistinct: rename_func("approx_count_distinct"),
            exp.Stddev: rename_func("stdev"),
            exp.StddevPop: rename_func("stdevp"),
            exp.StddevSamp: rename_func("stdev"),
            exp.Variance: rename_func("var"),
            exp.VariancePop: rename_func("varp"),
            exp.Ceil: rename_func("ceiling"),
            exp.Trim: lambda self, e: f"TRIM({e.this.sql(self.dialect)})",
            exp.DateFromParts: rename_func("datefromparts"),
            exp.Greatest: _greatest,
            exp.Least: _least,
            exp.Ln: rename_func("log"),
            exp.Select: transforms.preprocess(
                [
                    transforms.eliminate_semi_and_anti_joins,
                    hex_sl_eliminate_qualify,
                ]
            ),
        }

    class Tokenizer(TSQL.Tokenizer):
        # Override VAR_SINGLE_TOKENS to remove $ - we handle it as PARAMETER instead
        VAR_SINGLE_TOKENS: ClassVar[set[str]] = {"@", "#"}

        # Add $ as PARAMETER token so ${...} can be parsed as placeholders
        SINGLE_TOKENS: ClassVar[dict[str, TokenType]] = {
            **tokens.Tokenizer.SINGLE_TOKENS,
            "$": TokenType.PARAMETER,
        }

    class Parser(TSQL.Parser):
        PLACEHOLDER_PARSERS = placeholder_parser_mapping(
            TSQL.Parser.PLACEHOLDER_PARSERS
        )

        def _parse_placeholder(self) -> exp.Expression | None:
            return parse_jinja_placeholder(self)

        # sqlglot tries to convert DATEPART to FORMAT, but SQL Server 2018
        # supports DATEPART directly
        FUNCTIONS = TSQL.Parser.FUNCTIONS.copy()
        FUNCTIONS["DATEPART"] = _build_datepart
