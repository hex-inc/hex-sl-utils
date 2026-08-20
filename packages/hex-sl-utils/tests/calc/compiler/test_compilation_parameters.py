from inline_snapshot import snapshot

from hex_sl_utils.calc.parser import parse_calc_expression
from hex_sl_utils.datatype import DataType
from hex_sl_utils.dialect.clickhouse import ClickHouse
from hex_sl_utils.expr import ExpressionContext


# Unary Operators
def test_parameter_compilation():
    dialect = ClickHouse()
    calc_expr = parse_calc_expression("42 + {{a}}")
    columns = {}

    typed_expr = dialect.compile_calc_expr(
        calc_expr,
        ExpressionContext.PROJECTION,
        columns,
        "America/New_York",
        parameters={"a": DataType.NUMBER, "b": DataType.STRING},
    )

    assert typed_expr.expression.sql(dialect=dialect.sqlglot_dialect()) == snapshot(
        "42 + {{a}}"
    )
