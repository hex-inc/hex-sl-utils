from inline_snapshot import snapshot

from hex_sl_utils._vendor.sqlglot import exp
from hex_sl_utils.calc.parser import parse_calc_expression
from hex_sl_utils.datatype import DataType
from hex_sl_utils.dialect.clickhouse import ClickHouse
from hex_sl_utils.expr import (
    ExpressionContext,
    ExpressionKind,
    TypedSelectExpression,
)


# Unary Operators
def test_compilation_substitution():
    dialect = ClickHouse()
    calc_expr = parse_calc_expression("42 + a")
    columns = {}
    substitutions = {
        "a": TypedSelectExpression(
            expression=exp.Literal.number(12),
            data_type=DataType.NUMBER,
            kind=ExpressionKind.SCALAR,
        )
    }

    typed_expr = dialect.compile_calc_expr(
        calc_expr,
        ExpressionContext.PROJECTION,
        columns,
        "America/New_York",
        parameters={},
        substitutions=substitutions,
    )

    assert typed_expr.expression.sql() == snapshot("42 + 12")
