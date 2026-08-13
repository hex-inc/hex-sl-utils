from hex_sl.calc.parser import parse_calc_expression

from hex_sl.datatype import DataType
from hex_sl.dialect.clickhouse import HexSLClickHouse
from hex_sl.expr import ExpressionContext, ExpressionKind, TypedSelectExpression

from hex_sl._vendor.sqlglot import exp

from inline_snapshot import snapshot

from hex_sl.schema import Schema


# Unary Operators
def test_compilation_substitution():
    dialect = HexSLClickHouse()
    calc_expr = parse_calc_expression("42 + a")
    schema = Schema(name="test_schema", types={})
    substitutions = {
        "a": TypedSelectExpression(
            expression=exp.Literal.number(12),
            data_type=DataType.NUMBER,
            kind=ExpressionKind.SCALAR,
        )
    }

    typed_expr = dialect.compile_expression(
        calc_expr,
        ExpressionContext.PROJECTION,
        schema,
        "America/New_York",
        parameters={},
        substitutions=substitutions,
    )

    assert typed_expr.expression.sql() == snapshot("42 + 12")
