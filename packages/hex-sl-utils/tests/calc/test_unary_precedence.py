"""Tests for unary operator precedence and parenthesization."""

import pytest
from inline_snapshot import snapshot

from hex_sl.calc.ast.literals import LiteralBool, LiteralNumber
from hex_sl.calc.ast.binary import (
    BinaryPlus,
    BinaryMultiply,
    BinaryAnd,
    BinaryOr,
    BinaryPower,
)
from hex_sl.calc.ast.unary import UnaryMinus, UnaryNot
from hex_sl.calc.compiler import CalcToTypedSelectVisitor
from hex_sl.dialect.base import HexSLDialect
from hex_sl.expr import ExpressionContext
from hex_sl.schema import Schema


@pytest.fixture
def visitor() -> CalcToTypedSelectVisitor:
    """Create a visitor for compiling calc expressions."""
    schema = Schema(name="test_schema", types={})
    dialect = HexSLDialect.from_name("duckdb")
    return CalcToTypedSelectVisitor(
        dialect,
        ExpressionContext.PROJECTION,
        schema,
        timezone="UTC",
    )


class TestUnaryPrecedence:
    """Test unary operator precedence and parenthesization."""

    def test_unary_minus_with_addition(self, visitor):
        """Test -(a + b) requires parentheses."""
        # Create expression: -(5 + 3)
        add_expr = BinaryPlus(lhs=LiteralNumber(number=5), rhs=LiteralNumber(number=3))
        neg_expr = UnaryMinus(arg=add_expr)
        result = visitor.visit_unary(neg_expr)

        # Should generate -(5 + 3), not -5 + 3
        assert result.expression.sql() == snapshot("-(5 + 3)")

    def test_unary_minus_with_multiplication(self, visitor):
        """Test -(a * b) requires parentheses."""
        # Create expression: -(5 * 3)
        mult_expr = BinaryMultiply(
            lhs=LiteralNumber(number=5), rhs=LiteralNumber(number=3)
        )
        neg_expr = UnaryMinus(arg=mult_expr)
        result = visitor.visit_unary(neg_expr)

        # Should generate -(5 * 3), not -5 * 3
        assert result.expression.sql() == snapshot("-(5 * 3)")

    def test_unary_minus_simple(self, visitor):
        """Test -a doesn't need parentheses."""
        # Create expression: -5
        neg_expr = UnaryMinus(arg=LiteralNumber(number=5))
        result = visitor.visit_unary(neg_expr)

        # Should generate -5
        assert result.expression.sql() == snapshot("-5")

    def test_unary_not_with_and(self, visitor):
        """Test !(a && b) requires parentheses."""
        # Create expression: !(true && false)
        and_expr = BinaryAnd(lhs=LiteralBool(bool=True), rhs=LiteralBool(bool=False))
        not_expr = UnaryNot(arg=and_expr)
        result = visitor.visit_unary(not_expr)

        # Should generate NOT (TRUE AND FALSE), not NOT TRUE AND FALSE
        assert result.expression.sql() == snapshot("NOT (TRUE AND FALSE)")

    def test_unary_not_with_or(self, visitor):
        """Test !(a || b) requires parentheses."""
        # Create expression: !(true || false)
        or_expr = BinaryOr(lhs=LiteralBool(bool=True), rhs=LiteralBool(bool=False))
        not_expr = UnaryNot(arg=or_expr)
        result = visitor.visit_unary(not_expr)

        # Should generate NOT (TRUE OR FALSE), not NOT TRUE OR FALSE
        assert result.expression.sql() == snapshot("NOT (TRUE OR FALSE)")

    def test_unary_not_simple(self, visitor):
        """Test !a doesn't need parentheses."""
        # Create expression: !true
        not_expr = UnaryNot(arg=LiteralBool(bool=True))
        result = visitor.visit_unary(not_expr)

        # Should generate NOT TRUE
        assert result.expression.sql() == snapshot("NOT TRUE")

    def test_unary_minus_with_power(self, visitor):
        """Test -(a ^ b) requires parentheses."""
        # Create expression: -(2 ^ 3)
        pow_expr = BinaryPower(lhs=LiteralNumber(number=2), rhs=LiteralNumber(number=3))
        neg_expr = UnaryMinus(arg=pow_expr)
        result = visitor.visit_unary(neg_expr)

        # Should generate -(POWER(2, 3))
        assert result.expression.sql() == snapshot("-(POWER(2, 3))")

    def test_nested_unary_operators(self, visitor):
        """Test nested unary operators: -(-a)."""
        # Create expression: -(-5)
        inner_neg = UnaryMinus(arg=LiteralNumber(number=5))
        outer_neg = UnaryMinus(arg=inner_neg)
        result = visitor.visit_unary(outer_neg)

        # Should generate -(-5) with parentheses for clarity
        assert result.expression.sql() == "-(-5)"

    def test_unary_not_with_is_null(self, visitor):
        """Test NOT v IS NULL doesn't add extra parentheses."""
        # We can't directly create IS NULL through the calc AST, but we can
        # verify the helper function behavior
        from hex_sl._vendor.sqlglot import exp
        from hex_sl.calc.parentheses import parens_if_needed

        # Create IS NULL expression
        is_null = exp.Is(this=exp.column("carrier"), expression=exp.Null())

        # IS NULL should not need parentheses when used with unary NOT
        result = parens_if_needed(is_null, "!", operand_type="unary")
        assert result is is_null  # Should return the same expression, not wrapped


if __name__ == "__main__":
    pytest.main([__file__])
