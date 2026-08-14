"""Copied HexSL inline-VALUES query builder for calc result tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

from hex_sl._vendor.sqlglot import exp, to_identifier
from hex_sl.expr import ExpressionContext, TypedSelectExpression

if TYPE_CHECKING:
    import polars as pl

    from hex_sl.datatype import DataType
    from hex_sl.dialect.base import HexSLDialect
    from hex_sl.schema import Schema


def build_values_query_for_df(
    table: pl.DataFrame,
    dialect: HexSLDialect,
    table_alias: str = "t",
) -> tuple[exp.Select, Schema]:
    """
    Build a sqlglot Select expression with inline VALUES from a Polars DataFrame
    """

    from hex_sl.calc.ast.column import unmangle
    from hex_sl.datatype import datatype_to_sqlglot
    from hex_sl.schema import Schema

    schema: Schema = Schema.from_polars(table, table_alias)
    cols = table.columns
    rows = []

    for row in table.iter_rows():
        typed_exprs = []
        for col, value in zip(cols, row):
            data_type: DataType = schema.types[unmangle(col)]

            # Handle None by casting the NULL literal
            if value is None:
                null_expr: exp.Expression
                if dialect.null_literals_should_be_cast_to_type():
                    null_expr = exp.cast(exp.null(), to=datatype_to_sqlglot(data_type))
                else:
                    null_expr = exp.null()

                typed_exprs.append(
                    TypedSelectExpression.from_sqlglot(
                        expression=null_expr,
                        data_type=data_type,
                    )
                )
            # Otherwise, compile the literal with ibis
            else:
                typed_exprs.append(
                    dialect.compile_literal(value, context=ExpressionContext.PROJECTION)
                )

        rows.append(exp.Tuple(expressions=[expr.expression for expr in typed_exprs]))

    values_query = (
        exp.Select()
        .from_(
            exp.Values(
                expressions=rows,
                alias=exp.TableAlias(
                    this=to_identifier(table_alias, quoted=True),
                    columns=[exp.to_identifier(col, quoted=True) for col in cols],
                ),
            )
        )
        .select("*", copy=False)
    )

    return values_query, schema
