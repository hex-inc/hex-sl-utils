from hex_sl.calc.agg_extraction import (
    AggregateExtractionVisitor,
)

from hex_sl.calc.ast.binary.math import BinaryMultiply, BinaryPlus
from hex_sl.calc.ast.column import Column
from hex_sl.calc.ast.functions.aggs import FuncAvg, FuncSum
from hex_sl.calc.visitor import CalcToStringVisitor
from inline_snapshot import snapshot


def test_aggregate_replacement_visitor():
    # Create a test expression: avg(col1) + sum(col2 * col3)
    col1 = Column(name="col1")
    col2 = Column(name="col2")
    col3 = Column(name="col3")

    avg_expr = FuncAvg(args=[col1])
    mul_expr = BinaryMultiply(lhs=col2, rhs=col3)
    sum_expr = FuncSum(args=[mul_expr])

    expr = BinaryPlus(lhs=avg_expr, rhs=sum_expr)

    # Use the visitor to replace aggregate expressions
    from hex_sl.dialect.duckdb import HexSLDuckDB

    dialect = HexSLDuckDB()
    visitor = AggregateExtractionVisitor(dialect)
    modified_expr, column_to_agg = expr.accept(visitor)

    # Verify the result
    to_string = CalcToStringVisitor()
    result_str = modified_expr.accept(to_string)

    assert "(_agg_0 + _agg_1)" == result_str

    # Verify the mapping
    assert len(column_to_agg) == 2

    # Convert the original expressions to strings for comparison
    assert {k: v.accept(to_string) for k, v in column_to_agg.items()} == snapshot(
        {
            "_agg_0": "avg(col1)",
            "_agg_1": "sum((col2 * col3))",
        }
    )
