from inline_snapshot import snapshot

from hex_sl_utils.calc.ast.literals import LiteralBool, LiteralNumber
from hex_sl_utils.calc.ast.unary import UnaryMinus, UnaryNot, UnaryPlus
from hex_sl_utils.calc.compiler import CalcToTypedSelectVisitor
from hex_sl_utils.datatype import DataType
from hex_sl_utils.expr import ExpressionKind


# Unary Operators
def test_unary_minus(visitor: CalcToTypedSelectVisitor):
    arg = LiteralNumber(number=42)
    unary = UnaryMinus(arg=arg)
    result = visitor.visit_unary(unary)
    assert result.expression.sql() == snapshot("-42")
    assert result.data_type == DataType.NUMBER
    assert result.kind == ExpressionKind.SCALAR


def test_unary_plus(visitor: CalcToTypedSelectVisitor):
    arg = LiteralNumber(number=42.0)
    unary = UnaryPlus(arg=arg)
    result = visitor.visit_unary(unary)
    assert result.expression.sql() == snapshot("42.0")
    assert result.data_type == DataType.NUMBER
    assert result.kind == ExpressionKind.SCALAR


def test_unary_not(visitor: CalcToTypedSelectVisitor):
    arg = LiteralBool(bool=True)
    unary = UnaryNot(arg=arg)
    result = visitor.visit_unary(unary)
    assert result.expression.sql() == snapshot("NOT TRUE")
    assert result.data_type == DataType.BOOLEAN
    assert result.kind == ExpressionKind.SCALAR
