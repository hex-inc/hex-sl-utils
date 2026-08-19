from __future__ import annotations

import datetime
from typing import Any

from hex_sl_utils._vendor.sqlglot import exp, transforms
from hex_sl_utils._vendor.sqlglot.dialects.dialect import rename_func
from hex_sl_utils._vendor.sqlglot.dialects.redshift import Redshift as SqlGlotRedshift
from hex_sl_utils._vendor.sqlglot.tokens import TokenType
from hex_sl_utils.datatype import DataType
from hex_sl_utils.dialect.dialect_name import DialectName
from hex_sl_utils.dialect.postgres import Postgres
from hex_sl_utils.dialect.transforms import (
    hex_sl_eliminate_qualify,
    values_as_union_with_consistent_names_sql,
)
from hex_sl_utils.expr import ExpressionContext, ExpressionKind, TypedSelectExpression
from hex_sl_utils.placeholder import (
    PlaceholderGeneratorMixin,
    parse_jinja_placeholder,
    placeholder_parser_mapping,
    placeholder_sql,
)
from hex_sl_utils.time import TimeTruncUnit


class Redshift(Postgres):
    @classmethod
    def name(cls) -> DialectName:
        return "redshift"

    @classmethod
    def sqlglot_dialect(cls) -> str:
        return "hex-sl-redshift"

    def supports_median(self) -> bool:
        # Unlike postgres, redshift does not support median
        return False

    def supports_percentile_exact(self) -> bool:
        # Redshift supports PERCENTILE_CONT with WITHIN GROUP, but has a
        # severe limitation: all WITHIN GROUP ORDER BY clauses in the same
        # query must be identical. This makes it impractical for HexSL where
        # we need to compute percentiles on different columns.
        return False

    def supports_percentile_approx(self) -> bool:
        # Redshift's APPROXIMATE PERCENTILE_DISC has two limitations:
        # 1. The multi-word function name cannot currently be parsed by
        #    sqlglot (though it can generate it)
        # 2. Like exact percentiles, all WITHIN GROUP ORDER BY clauses must
        #    be identical in one query
        # The second limitation makes it impractical for HexSL regardless of
        # the first issue.
        return False

    def null_literals_should_be_cast_to_type(self) -> bool:
        return True

    def compile_literal(
        self,
        literal: Any,
        context: ExpressionContext | None = None,
        data_type: DataType | None = None,
    ) -> TypedSelectExpression:
        if isinstance(literal, datetime.datetime):
            # Handle datetime objects with Redshift-specific CAST functions
            if literal.tzinfo is not None:
                # This is a timezone-aware datetime (TIMESTAMPTZ)
                # Use isoformat() to get 'T' separator and proper timezone format
                dt_str = literal.isoformat()
                ts_expr = exp.Cast(
                    this=exp.Literal.string(dt_str),
                    to=exp.DataType.build("TIMESTAMP WITH TIME ZONE"),
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
        elif type(literal) == datetime.date:
            # Redshift doesn't seem to have the `DATE_FROM_PARTS` function,
            # we just use a CAST
            return TypedSelectExpression.from_sqlglot(
                exp.Cast(
                    this=exp.Literal.string(literal.strftime("%Y-%m-%d")),
                    to=exp.DataType.build("DATE"),
                ),
                DataType.DATE,
                ExpressionKind.SCALAR,
            )
        elif isinstance(literal, str):
            # Redshift seems to need an explicit cast to string in some situations to
            # avoid a "failed to find conversion function from "unknown" to text" error
            typed_expr = super().compile_literal(literal)
            return TypedSelectExpression(
                expression=exp.Cast(
                    this=typed_expr.expression, to=exp.DataType.build("TEXT")
                ),
                data_type=typed_expr.data_type,
                kind=typed_expr.kind,
            )

        return super().compile_literal(literal)

    def datetime_to_epoch_ms(self, arg: TypedSelectExpression) -> TypedSelectExpression:
        """
        Build expression to convert a timestamp to epoch milliseconds.
        """

        if arg.data_type == DataType.TIMESTAMPTZ:
            # Always convert to UTC before extracting epoch millis
            arg = self.at_timezone(arg, "UTC")

        expr: exp.Expression = exp.Mul(
            this=exp.cast(
                exp.Extract(
                    this=exp.Literal.string("epoch"), expression=arg.expression
                ),
                to=exp.DataType.build("BIGINT"),
            ),
            expression=exp.Literal.number(1000),
        )
        if arg.data_type != DataType.DATE:
            millis = exp.cast(
                exp.Extract(
                    this=exp.Literal.string("millisecond"), expression=arg.expression
                ),
                to=exp.DataType.build("BIGINT"),
            )
            expr = exp.Paren(
                this=exp.Add(
                    this=exp.Paren(this=millis),
                    expression=exp.Paren(this=expr),
                )
            )

        return TypedSelectExpression.from_sqlglot(
            expr,
            DataType.NUMBER,
            kind=arg.kind,
        )

    def epoch_ms_to_timestamp(
        self, arg: TypedSelectExpression
    ) -> TypedSelectExpression:
        """
        Build expression to convert epoch milliseconds to a timestamp.
        """

        # (TIMESTAMP 'epoch' + ((arg_expression / 1000) * INTERVAL '1 second'))
        return TypedSelectExpression.from_sqlglot(
            exp.Paren(
                this=exp.Add(
                    this=exp.Cast(
                        this=exp.Literal.string("epoch"),
                        to=exp.DataType.build("TIMESTAMP"),
                    ),
                    expression=exp.Paren(
                        this=exp.Mul(
                            this=exp.Paren(
                                this=exp.Div(
                                    this=exp.paren(arg.expression),
                                    expression=exp.Literal.number(1000),
                                )
                            ),
                            expression=exp.Interval(  # type: ignore[no-untyped-call]
                                this=exp.Literal.string("1"),
                                unit=exp.Var(this="SECOND"),
                            ),
                        )
                    ),
                )
            ),
            DataType.TIMESTAMPTZ,
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
            exp.AtTimeZone(this=arg.expression, zone=exp.Literal.string(convert_tz))
            if convert_tz is not None
            else arg.expression
        )

        date_trunc_expr: exp.Expression
        if unit == "week":
            date_trunc_expr = exp.Paren(
                this=exp.Sub(
                    this=self.func(
                        "DATE_TRUNC",
                        exp.Literal.string(unit),
                        exp.Add(
                            this=exp.Paren(this=tz_expression),
                            expression=exp.Interval(  # type: ignore[no-untyped-call]
                                this=exp.Literal.string("1"), unit="day"
                            ),
                        ),
                    ),
                    expression=exp.Interval(this=exp.Literal.string("1"), unit="day"),  # type: ignore[no-untyped-call]
                )
            )
        else:
            sql_unit = "week" if unit == "weekmonday" else unit
            # Build the DATE_TRUNC function call
            date_trunc_expr = self.func(
                "DATE_TRUNC", exp.Literal.string(sql_unit), tz_expression
            )

        if arg.data_type == DataType.DATE:
            date_trunc_expr = exp.Cast(
                this=date_trunc_expr, to=exp.DataType.build("DATE")
            )

        # Re-apply timezone if provided
        if convert_tz is not None:
            date_trunc_expr = exp.AtTimeZone(
                this=date_trunc_expr, zone=exp.Literal.string(convert_tz)
            )

        return TypedSelectExpression.from_sqlglot(
            date_trunc_expr,
            arg.data_type,
            kind=arg.kind,
        )

    def splitpart(
        self,
        string: TypedSelectExpression,
        delimiter: TypedSelectExpression,
        part_number: TypedSelectExpression,
    ) -> TypedSelectExpression:
        """Redshift has a built-in SPLIT_PART function."""

        kind = ExpressionKind._validate_infer_kind(
            [string.kind, delimiter.kind, part_number.kind]
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
        Redshift-specific startswith implementation using LEFT/LENGTH approach.
        """

        kind = ExpressionKind._validate_infer_kind([string.kind, prefix.kind])
        prefix_length = exp.Length(this=prefix.expression)
        left_expr = exp.Left(this=string.expression, expression=prefix_length)
        eq_expr = exp.EQ(this=left_expr, expression=prefix.expression)
        return TypedSelectExpression.from_sqlglot(eq_expr, DataType.BOOLEAN, kind)

    def endswith(
        self, string: TypedSelectExpression, suffix: TypedSelectExpression
    ) -> TypedSelectExpression:
        """
        Redshift-specific endswith implementation using RIGHT/LENGTH approach.
        """

        kind = ExpressionKind._validate_infer_kind([string.kind, suffix.kind])
        suffix_length = exp.Length(this=suffix.expression)
        right_expr = exp.Right(this=string.expression, expression=suffix_length)
        eq_expr = exp.EQ(this=right_expr, expression=suffix.expression)
        return TypedSelectExpression.from_sqlglot(eq_expr, DataType.BOOLEAN, kind)

    def concat(self, *args: TypedSelectExpression) -> TypedSelectExpression:
        """
        Build a CONCAT expression that treats NULLs as empty strings for Redshift.

        Redshift's || operator returns NULL if any argument is NULL, so we need to wrap
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
            # Use DPipe (||) for Redshift concatenation
            concat_expr: exp.Expression = coalesced_args[0]
            for arg in coalesced_args[1:]:
                concat_expr = exp.DPipe(this=concat_expr, expression=arg)
            return TypedSelectExpression.from_sqlglot(
                concat_expr, DataType.STRING, kind
            )


class RedshiftSqlGlotOverride(SqlGlotRedshift):
    @classmethod
    def dialect_name(cls) -> str:
        return "hex-sl-redshift"

    class Generator(PlaceholderGeneratorMixin, SqlGlotRedshift.Generator):
        TRANSFORMS = SqlGlotRedshift.Generator.TRANSFORMS.copy() | {
            exp.Mod: rename_func("mod"),
            exp.Select: transforms.preprocess(
                [
                    transforms.eliminate_semi_and_anti_joins,
                    hex_sl_eliminate_qualify,
                ]
            ),
        }

        def placeholder_sql(self, expression: exp.Placeholder) -> str:
            return placeholder_sql(self, expression)

        def values_sql(
            self, expression: exp.Values, values_as_table: bool = True
        ) -> str:
            return values_as_union_with_consistent_names_sql(self, expression)

    class Parser(SqlGlotRedshift.Parser):
        PLACEHOLDER_PARSERS = placeholder_parser_mapping(
            SqlGlotRedshift.Parser.PLACEHOLDER_PARSERS,
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
