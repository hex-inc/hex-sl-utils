from hex_sl.calc.parser import parse_calc_expression

from hex_sl.datatype import DataType
from hex_sl.dialect.clickhouse import HexSLClickHouse
from hex_sl.expr import ExpressionContext


from inline_snapshot import snapshot

from hex_sl.schema import Schema


# Unary Operators
def test_parameter_compilation():
    dialect = HexSLClickHouse()
    calc_expr = parse_calc_expression("42 + {{a}}")
    schema = Schema(name="test_schema", types={})

    typed_expr = dialect.compile_expression(
        calc_expr,
        ExpressionContext.PROJECTION,
        schema,
        "America/New_York",
        parameters={"a": DataType.NUMBER, "b": DataType.STRING},
    )

    assert typed_expr.expression.sql(dialect=dialect.sqlglot_dialect()) == snapshot(
        "42 + {{a}}"
    )
