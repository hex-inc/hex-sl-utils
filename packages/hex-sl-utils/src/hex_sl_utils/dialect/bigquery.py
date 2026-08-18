from __future__ import annotations

import datetime
from typing import Any, ClassVar

from hex_sl_utils._vendor.sqlglot import exp, tokens
from hex_sl_utils._vendor.sqlglot.dialects.bigquery import BigQuery as SqlGlotBigQuery
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


class BigQuery(Dialect):
    @classmethod
    def name(cls) -> DialectName:
        return "bigquery"

    @classmethod
    def sqlglot_dialect(cls) -> str:
        return "hex-sl-bigquery"

    def truncates_on_integer_division(self) -> bool:
        return False

    def mod_supports_floats(self) -> bool:
        return False

    def supports_median(self) -> bool:
        return False

    def supports_non_finite_floats(self) -> bool:
        return True

    def build_isnan(self, arg: TypedSelectExpression) -> TypedSelectExpression:
        """
        Build an IS NAN check using BigQuery's native IS_NAN function.
        """

        # Use BigQuery's native IS_NAN function
        cast_arg = self.cast_to_float(arg)
        isnan_expr = self.func("IS_NAN", cast_arg.expression)

        return TypedSelectExpression.from_sqlglot(
            isnan_expr, DataType.BOOLEAN, arg.kind
        )

    def supports_percentile_approx(self) -> bool:
        return True

    def build_percentile_approx(
        self,
        arg: TypedSelectExpression,
        percentile: float,
    ) -> TypedSelectExpression:
        cast_typed = self.cast_to_float(arg)
        quantiles_expr = self.func(
            "APPROX_QUANTILES", cast_typed.expression, exp.Literal.number(100)
        )
        index = int(percentile * 100)
        percentile_expr = exp.Bracket(
            this=quantiles_expr,
            expressions=[exp.Literal.number(index)],
            offset=0,
        )

        return TypedSelectExpression.from_sqlglot(
            percentile_expr, DataType.NUMBER, arg.kind
        )

    def datetime_to_epoch_ms(self, arg: TypedSelectExpression) -> TypedSelectExpression:
        """
        Build expression to convert a timestamp to epoch milliseconds.
        """

        if arg.data_type == DataType.DATE:
            # BigQuery doesn't support the unix_seconds function on dates directly,
            # and casting to a timestamp with ibis results in a Datetime type, which
            # also doesn't support the unix_seconds function. So we need to cast
            # to a timestamp first.
            return TypedSelectExpression.from_sqlglot(
                exp.If(
                    this=exp.Not(
                        this=exp.Is(this=arg.expression, expression=exp.Null())
                    ),
                    true=exp.Mul(
                        this=exp.UnixDate(this=arg.expression),
                        expression=exp.Literal.number(86400000),
                    ),
                    false=exp.Null(),
                ),
                DataType.NUMBER,
                kind=arg.kind,
            )
        elif arg.data_type == DataType.TIMESTAMP:
            # IF(
            #   NOT (arg_expression IS NULL),
            #   UNIX_MILLIS(TIMESTAMP(arg)),
            #   NULL
            # )
            return TypedSelectExpression.from_sqlglot(
                exp.If(
                    this=exp.Not(
                        this=exp.Is(this=arg.expression, expression=exp.Null())
                    ),
                    true=exp.Anonymous(
                        this="UNIX_MILLIS",
                        expressions=[exp.Timestamp(this=arg.expression)],
                    ),
                    false=exp.Null(),
                ),
                DataType.NUMBER,
                kind=arg.kind,
            )
        else:
            # IF(
            #   NOT (arg_expression IS NULL),
            #   UNIX_MILLIS(TIMESTAMP(DATETIME(arg, 'UTC'))),
            #   NULL
            # )
            return TypedSelectExpression.from_sqlglot(
                exp.If(
                    this=exp.Not(
                        this=exp.Is(this=arg.expression, expression=exp.Null())
                    ),
                    true=exp.Anonymous(
                        this="UNIX_MILLIS",
                        expressions=[
                            exp.Timestamp(
                                this=exp.Anonymous(
                                    this="DATETIME",
                                    expressions=[
                                        arg.expression,
                                        exp.Literal.string("UTC"),
                                    ],
                                )
                            )
                        ],
                    ),
                    false=exp.Null(),
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
        convert_tz = tz if arg.data_type == DataType.TIMESTAMPTZ else None
        sql_unit = "WEEK(MONDAY)" if unit == "weekmonday" else unit

        # Determine the function name based on whether a timezone is provided
        if convert_tz:
            # Build the function call
            expression = self.func(
                "TIMESTAMP_TRUNC",
                arg.expression,
                exp.Literal.string(sql_unit.upper()),
                exp.Literal.string(convert_tz),
            )
        else:
            # Build the function call
            expression = exp.DateTrunc(  # type: ignore[no-untyped-call]
                unit=exp.Literal.string(sql_unit.upper()),
                this=arg.expression,
            )

        if arg.data_type == DataType.DATE:
            expression = exp.Cast(this=expression, to=exp.DataType.build("DATE"))

        return TypedSelectExpression.from_sqlglot(
            expression,
            arg.data_type,
            kind=arg.kind,
        )

    def epoch_ms_to_timestamp(
        self,
        arg: TypedSelectExpression,
    ) -> TypedSelectExpression:
        """
        Build expression to convert epoch milliseconds to a timestamp.
        """

        ts_utc = exp.Anonymous(
            this="timestamp_millis",
            expressions=[exp.Cast(this=self.func("trunc", arg.expression), to="INT64")],
        )
        return TypedSelectExpression.from_sqlglot(
            ts_utc,
            DataType.TIMESTAMPTZ,
            kind=arg.kind,
        )

    def at_timezone(self, arg: TypedSelectExpression, tz: str) -> TypedSelectExpression:
        if arg.data_type == DataType.TIMESTAMPTZ:
            return TypedSelectExpression.from_sqlglot(
                self.func("DATETIME", arg.expression, exp.Literal.string(tz)),
                DataType.TIMESTAMP,
                kind=arg.kind,
            )
        else:
            return TypedSelectExpression.from_sqlglot(
                self.func("TIMESTAMP", arg.expression, exp.Literal.string(tz)),
                DataType.TIMESTAMPTZ,
                kind=arg.kind,
            )

    def build_division(
        self, left: TypedSelectExpression, right: TypedSelectExpression
    ) -> TypedSelectExpression:
        """
        Build a division expression using BigQuery's ieee_divide function.

        Args:
            left: The dividend
            right: The divisor

        Returns:
            A TypedSelectExpression representing the division
        """

        # Use ieee_divide for BigQuery
        div_expr = self.func("ieee_divide", left.expression, right.expression)

        # Determine expression kind
        kind = ExpressionKind._validate_infer_kind([left.kind, right.kind])

        # For numeric division, result is NUMBER
        return TypedSelectExpression.from_sqlglot(div_expr, DataType.NUMBER, kind)

    def compile_literal(
        self,
        literal: Any,
        context: ExpressionContext | None = None,
        data_type: DataType | None = None,
    ) -> TypedSelectExpression:
        """
        Compile a literal expression with proper type handling for BigQuery.

        BigQuery uses TIMESTAMP for timestamptz and DATETIME for timestamp.
        """
        # Handle datetime objects with BigQuery-specific functions

        if isinstance(literal, datetime.datetime):
            # Check if datetime has timezone info
            if literal.tzinfo is not None:
                # This is a timezone-aware datetime (TIMESTAMPTZ)
                # BigQuery uses TIMESTAMP() function for timestamptz
                dt_str = literal.isoformat()
                ts_expr = self.func("TIMESTAMP", exp.Literal.string(dt_str))
                result = TypedSelectExpression.from_sqlglot(
                    ts_expr, DataType.TIMESTAMPTZ, ExpressionKind.SCALAR
                )
            else:
                # This is a naive datetime (TIMESTAMP)
                # BigQuery uses DATETIME() function for timestamp
                # Use isoformat() to get 'T' separator for consistency with
                # expected snapshots
                dt_str = literal.isoformat()
                ts_expr = self.func("DATETIME", exp.Literal.string(dt_str))
                result = TypedSelectExpression.from_sqlglot(
                    ts_expr, DataType.TIMESTAMP, ExpressionKind.SCALAR
                )

            if context is not None:
                result = self.wrap_expression_for_context(result, context)
            return result

        # Handle date objects with BigQuery-specific DATE function
        elif isinstance(literal, datetime.date) and not isinstance(
            literal, datetime.datetime
        ):
            # Use DATE(year, month, day) for BigQuery
            date_expr = self.func(
                "DATE",
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

    def startswith(
        self, string: TypedSelectExpression, prefix: TypedSelectExpression
    ) -> TypedSelectExpression:
        """
        BigQuery-specific startswith implementation using native STARTS_WITH function.
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
        BigQuery-specific endswith implementation using native ends_with function.
        """

        kind = ExpressionKind._validate_infer_kind([string.kind, suffix.kind])
        endswith_expr = self.func("ENDS_WITH", string.expression, suffix.expression)
        return TypedSelectExpression.from_sqlglot(endswith_expr, DataType.BOOLEAN, kind)

    def concat(self, *args: TypedSelectExpression) -> TypedSelectExpression:
        """
        Build a CONCAT expression that treats NULLs as empty strings for BigQuery.

        BigQuery's CONCAT returns NULL if any argument is NULL, so we need to wrap
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

    def day_of_week_part(
        self,
        arg: TypedSelectExpression,
        timezone: str,
    ) -> TypedSelectExpression:
        """
        BigQuery-specific day of week implementation.

        BigQuery uses EXTRACT(DAYOFWEEK FROM date) which returns Sunday=1, Saturday=7.
        This already matches our expected format, so no adjustment needed.
        """

        if arg.data_type == DataType.TIMESTAMPTZ:
            arg = self.at_timezone(arg, timezone)

        # BigQuery EXTRACT(DAYOFWEEK FROM date) returns Sunday=1, Saturday=7
        dow_expr = exp.Extract(
            this=exp.Identifier(this="DAYOFWEEK"), expression=arg.expression
        )

        return TypedSelectExpression.from_sqlglot(dow_expr, DataType.NUMBER, arg.kind)

    def splitpart(
        self,
        string: TypedSelectExpression,
        delimiter: TypedSelectExpression,
        part_number: TypedSelectExpression,
    ) -> TypedSelectExpression:
        """
        BigQuery-specific splitpart implementation using IF, SPLIT, and safe_offset.

        Returns:
        IF(
          string IS NULL,
          NULL,
          COALESCE(
              SPLIT(string, delimiter)[safe_offset(
                  CAST(trunc(part_number) AS INT64) - 1
              )], ''
          )
        )
        """

        kind = ExpressionKind._validate_infer_kind(
            [
                string.kind,
                delimiter.kind,
                part_number.kind,
            ]
        )

        # Split the string
        split_expr = self.func("SPLIT", string.expression, delimiter.expression)

        # Convert 1-based part_number to 0-based index with proper casting
        # CAST(trunc(part_number) AS INT64) - 1
        truncated_part = self.func("trunc", part_number.expression)
        cast_part = exp.Cast(this=truncated_part, to=exp.DataType.build("INT64"))
        part_index = exp.Sub(this=cast_part, expression=exp.Literal.number(1))

        # Use safe_offset for array access
        safe_offset_expr = self.func("safe_offset", part_index)
        array_access = exp.Bracket(this=split_expr, expressions=[safe_offset_expr])

        # Wrap with COALESCE to return empty string if out of bounds
        coalesce_expr = exp.Coalesce(
            this=array_access, expressions=[exp.Literal.string("")]
        )

        # Handle null string case with IF
        result_expr = exp.If(
            this=exp.Is(this=string.expression, expression=exp.Null()),
            true=exp.Null(),
            false=coalesce_expr,
        )

        return TypedSelectExpression.from_sqlglot(result_expr, DataType.STRING, kind)

    def cast_to_int(self, arg: TypedSelectExpression) -> TypedSelectExpression:
        """
        Cast expression to integer type.

        BigQuery rounds when casting to INT64, so we need to use TRUNC first
        to ensure truncation behavior matches other databases.
        """

        # First truncate the value, then cast to INT64
        truncated = self.func("TRUNC", arg.expression)
        cast_expr = exp.Cast(this=truncated, to=exp.DataType.build("INT64"))
        return TypedSelectExpression.from_sqlglot(cast_expr, DataType.NUMBER, arg.kind)


class BigQuerySqlGlotOverride(SqlGlotBigQuery):
    @classmethod
    def dialect_name(cls) -> str:
        return "hex-sl-bigquery"

    class Generator(PlaceholderGeneratorMixin, SqlGlotBigQuery.Generator):
        def placeholder_sql(self, expression: exp.Placeholder) -> str:
            return placeholder_sql(self, expression)

    class Tokenizer(SqlGlotBigQuery.Tokenizer):
        # Add $ as PARAMETER token so ${...} can be parsed as placeholders
        SINGLE_TOKENS: ClassVar[dict[str, TokenType]] = {
            **tokens.Tokenizer.SINGLE_TOKENS,
            "$": TokenType.PARAMETER,
        }

    class Parser(SqlGlotBigQuery.Parser):
        PLACEHOLDER_PARSERS = placeholder_parser_mapping(
            SqlGlotBigQuery.Parser.PLACEHOLDER_PARSERS
        )

        def _parse_placeholder(self) -> exp.Expression | None:
            return parse_jinja_placeholder(self)

        def _parse_string(self) -> exp.Expression | None:
            """
            Override to handle BigQuery's FORMAT('string') syntax.

            When we're in a CAST context and just matched FORMAT token,
            check if the next token is a parenthesis.

            Note: This is non-standard (and not documented) syntax.
            sqlglot doesn't support it, but BigQuery accepts it.
            """
            # Check if we're parsing a format string (previous token was FORMAT)
            if (
                self._prev
                and self._prev.token_type == TokenType.FORMAT
                and self._curr
                and self._curr.token_type == TokenType.L_PAREN
            ):
                # Consume the left parenthesis
                self._advance()
                # Parse the string inside
                fmt_string = super()._parse_string()
                # Expect the right parenthesis
                if not self._match(TokenType.R_PAREN):  # type: ignore[no-untyped-call]
                    self.raise_error("Expected ) after FORMAT string")
                return fmt_string

            # Otherwise, use the default string parsing
            return super()._parse_string()
