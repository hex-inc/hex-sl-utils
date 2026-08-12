from inline_snapshot import snapshot

from hex_sl_utils.calc.ast.column import Column
from hex_sl_utils.calc.ast.expr import CalcExpr
from hex_sl_utils.calc.ast.literals import LiteralNumber, LiteralString
from hex_sl_utils.calc.parser import parse_calc_expression

from ._dialect import TestDialect


def test_substitute_column_with_literal():
    expression = "MyColumn"
    ast = parse_calc_expression(expression).root
    substitutions = {"MyColumn": LiteralNumber(number=42)}
    dialect = TestDialect()
    substituted_expr = CalcExpr(root=ast).substitute(substitutions, dialect)
    assert substituted_expr.root.to_string() == snapshot("42")


def test_substitute_column_with_expression():
    expression = "MyColumn + 1"
    ast = parse_calc_expression(expression).root
    substitutions = {"MyColumn": LiteralNumber(number=42)}
    dialect = TestDialect()
    substituted_expr = CalcExpr(root=ast).substitute(substitutions, dialect)
    assert substituted_expr.root.to_string() == snapshot("(42 + 1)")


def test_substitute_multiple_columns():
    expression = "Col1 + Col2"
    ast = parse_calc_expression(expression).root
    substitutions = {
        "Col1": LiteralNumber(number=10),
        "Col2": LiteralNumber(number=20),
    }
    dialect = TestDialect()
    substituted_expr = CalcExpr(root=ast).substitute(substitutions, dialect)
    assert substituted_expr.root.to_string() == snapshot("(10 + 20)")


def test_substitute_column_with_string():
    expression = "MyColumn"
    ast = parse_calc_expression(expression).root
    substitutions = {"MyColumn": LiteralString(str="hello")}
    dialect = TestDialect()
    substituted_expr = CalcExpr(root=ast).substitute(substitutions, dialect)
    assert substituted_expr.root.to_string() == snapshot('"hello"')


def test_substitute_column_with_another_column():
    expression = "MyColumn"
    ast = parse_calc_expression(expression).root
    substitutions = {"MyColumn": Column(name="AnotherColumn")}
    dialect = TestDialect()
    substituted_expr = CalcExpr(root=ast).substitute(substitutions, dialect)
    assert substituted_expr.root.to_string() == snapshot("AnotherColumn")


def test_substitute_no_match():
    expression = "MyColumn"
    ast = parse_calc_expression(expression).root
    substitutions = {"AnotherColumn": LiteralNumber(number=42)}
    dialect = TestDialect()
    substituted_expr = CalcExpr(root=ast).substitute(substitutions, dialect)
    assert substituted_expr.root.to_string() == snapshot("MyColumn")


def test_substitute_nested_expression():
    expression = "MyColumn + 1"
    ast = parse_calc_expression(expression).root
    substitutions = {"MyColumn": parse_calc_expression("2 * 3").root}
    dialect = TestDialect()
    substituted_expr = CalcExpr(root=ast).substitute(substitutions, dialect)
    assert substituted_expr.root.to_string() == snapshot("((2 * 3) + 1)")


def test_substitute_multiple_columns_and_functions():
    expression = "concat(Col1, ' ', Col2)"
    ast = parse_calc_expression(expression).root
    substitutions = {
        "Col1": LiteralString(str="hello"),
        "Col2": LiteralString(str="world"),
    }
    dialect = TestDialect()
    substituted_expr = CalcExpr(root=ast).substitute(substitutions, dialect)
    assert substituted_expr.root.to_string() == snapshot(
        'concat("hello", " ", "world")'
    )
