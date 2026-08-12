"""Tests for the unified parentheses system for calc language binary and unary expressions."""

import pytest
from inline_snapshot import snapshot

from hex_sl_utils._vendor.sqlglot import exp
from hex_sl_utils.calc.parentheses import (
    OPERATOR_PRECEDENCE,
    parens_if_needed,
)


def test_precedence_ordering():
    """Test that precedence values are correctly ordered."""
    # Verify the expected precedence hierarchy
    assert OPERATOR_PRECEDENCE["||"] < OPERATOR_PRECEDENCE["&&"]
    assert OPERATOR_PRECEDENCE["&&"] < OPERATOR_PRECEDENCE["="]
    assert OPERATOR_PRECEDENCE["="] < OPERATOR_PRECEDENCE["<"]
    assert OPERATOR_PRECEDENCE["<"] < OPERATOR_PRECEDENCE["+"]
    assert OPERATOR_PRECEDENCE["+"] < OPERATOR_PRECEDENCE["*"]
    assert OPERATOR_PRECEDENCE["*"] < OPERATOR_PRECEDENCE["^"]


def test_same_precedence_operators():
    """Test that operators with same precedence have identical values."""
    # Equality/inequality operators
    assert OPERATOR_PRECEDENCE["="] == OPERATOR_PRECEDENCE["!="]

    # Relational operators
    assert OPERATOR_PRECEDENCE["<"] == OPERATOR_PRECEDENCE["<="]
    assert OPERATOR_PRECEDENCE[">"] == OPERATOR_PRECEDENCE[">="]
    assert OPERATOR_PRECEDENCE["<"] == OPERATOR_PRECEDENCE[">"]

    # Additive operators
    assert OPERATOR_PRECEDENCE["+"] == OPERATOR_PRECEDENCE["-"]

    # Multiplicative operators
    assert OPERATOR_PRECEDENCE["*"] == OPERATOR_PRECEDENCE["/"]
    assert OPERATOR_PRECEDENCE["/"] == OPERATOR_PRECEDENCE["%"]


def test_no_wrapping_for_higher_precedence():
    """Higher precedence child should not be wrapped."""
    mult_expr = exp.Mul(this=exp.column("a"), expression=exp.column("b"))
    result = parens_if_needed(mult_expr, "+", operand_type="left")

    # Should return the same expression, not wrapped
    assert result is mult_expr
    assert not isinstance(result, exp.Paren)


def test_wrapping_for_lower_precedence():
    """Lower precedence child should be wrapped in parentheses."""
    add_expr = exp.Add(this=exp.column("a"), expression=exp.column("b"))
    result = parens_if_needed(add_expr, "*", operand_type="left")

    # Should be wrapped in parentheses
    assert isinstance(result, exp.Paren)
    assert result.this is add_expr


def test_no_wrapping_for_non_binary():
    """Non-binary expressions should never be wrapped."""
    literal = exp.Literal.number(42)
    column = exp.Column(this="test_col")

    for expr in [literal, column]:
        for op in OPERATOR_PRECEDENCE:
            result = parens_if_needed(expr, op, operand_type="left")
            assert result is expr
            assert not isinstance(result, exp.Paren)


def test_left_associative_same_precedence_left_operand():
    """Left operand with same precedence should not need parens."""
    sub_expr = exp.Sub(this=exp.column("a"), expression=exp.column("b"))
    result = parens_if_needed(sub_expr, "-", operand_type="left")

    # Left operand with same precedence doesn't need parens
    assert not isinstance(result, exp.Paren)
    assert result is sub_expr


def test_left_associative_same_precedence_right_operand():
    """Right operand with same precedence should need parens."""
    sub_expr = exp.Sub(this=exp.column("a"), expression=exp.column("b"))
    result = parens_if_needed(sub_expr, "-", operand_type="right")

    # Right operand with same precedence needs parens for left-associative ops
    assert isinstance(result, exp.Paren)
    assert result.this is sub_expr


def test_associativity_for_subtraction():
    """Test associativity for subtraction (a - (b - c) vs (a - b) - c)."""
    sub_expr = exp.Sub(this=exp.column("b"), expression=exp.column("c"))
    result = parens_if_needed(sub_expr, "-", operand_type="right")

    # Right operand needs parens for correct associativity
    assert isinstance(result, exp.Paren)
    assert result.this is sub_expr

    # Left operand doesn't need parens
    result = parens_if_needed(sub_expr, "-", operand_type="left")
    assert not isinstance(result, exp.Paren)
    assert result is sub_expr


def test_associativity_for_division():
    """Test associativity for division."""
    div_expr = exp.Div(this=exp.column("b"), expression=exp.column("c"))
    result = parens_if_needed(div_expr, "/", operand_type="right")

    # Right operand needs parens
    assert isinstance(result, exp.Paren)
    assert result.this is div_expr

    # Left operand doesn't need parens
    result = parens_if_needed(div_expr, "/", operand_type="left")
    assert not isinstance(result, exp.Paren)
    assert result is div_expr


def test_associativity_for_modulo():
    """Test associativity for modulo."""
    mod_expr = exp.Mod(this=exp.column("b"), expression=exp.column("c"))
    result = parens_if_needed(mod_expr, "%", operand_type="right")

    # Right operand needs parens
    assert isinstance(result, exp.Paren)
    assert result.this is mod_expr


def test_non_left_associative_operators():
    """Test that non-left-associative operators don't need special right-operand handling."""
    add_expr = exp.Add(this=exp.column("a"), expression=exp.column("b"))

    # Test left operand (should not need parens for same precedence)
    result_left = parens_if_needed(add_expr, "+", operand_type="left")
    assert not isinstance(result_left, exp.Paren)

    # Test right operand (should not need parens for same precedence)
    result_right = parens_if_needed(add_expr, "+", operand_type="right")
    assert not isinstance(result_right, exp.Paren)


def test_mixed_arithmetic_precedence():
    """Test a + b * c scenario."""
    mult_expr = exp.Mul(this=exp.column("b"), expression=exp.column("c"))
    result = parens_if_needed(mult_expr, "+", operand_type="left")

    # b * c has higher precedence than +, no parens needed
    assert not isinstance(result, exp.Paren)


def test_precedence_inversion():
    """Test (a + b) * c scenario."""
    add_expr = exp.Add(this=exp.column("a"), expression=exp.column("b"))
    result = parens_if_needed(add_expr, "*", operand_type="left")

    # a + b has lower precedence than *, parens needed
    assert isinstance(result, exp.Paren)
    assert result.this is add_expr


def test_logical_expression_precedence():
    """Test a && (b || c) scenario."""
    or_expr = exp.Or(this=exp.column("b"), expression=exp.column("c"))
    result = parens_if_needed(or_expr, "&&", operand_type="left")

    # OR has lower precedence than AND, parens needed
    assert isinstance(result, exp.Paren)
    assert result.this is or_expr


def test_comparison_and_logical():
    """Test a = b && c scenario."""
    eq_expr = exp.EQ(this=exp.column("a"), expression=exp.column("b"))
    result = parens_if_needed(eq_expr, "&&", operand_type="left")

    # Equality has higher precedence than AND, no parens needed
    assert not isinstance(result, exp.Paren)
    assert result is eq_expr


def test_chained_subtraction():
    """Test complex associativity scenarios for subtraction."""
    sub_expr = exp.Sub(this=exp.column("b"), expression=exp.column("c"))

    # Test a - (b - c) - left operand doesn't need parens
    result_left = parens_if_needed(sub_expr, "-", operand_type="left")
    assert not isinstance(result_left, exp.Paren)

    # Test a - (b - c) - right operand needs parens
    result_right = parens_if_needed(sub_expr, "-", operand_type="right")
    assert isinstance(result_right, exp.Paren)


def test_chained_division():
    """Test complex associativity scenarios for division."""
    div_expr = exp.Div(this=exp.column("b"), expression=exp.column("c"))

    # Test a / (b / c) - left operand doesn't need parens
    result_left = parens_if_needed(div_expr, "/", operand_type="left")
    assert not isinstance(result_left, exp.Paren)

    # Test a / (b / c) - right operand needs parens
    result_right = parens_if_needed(div_expr, "/", operand_type="right")
    assert isinstance(result_right, exp.Paren)


def test_unknown_child_operator():
    """Test with child expression type not mapped."""
    # Create a custom expression type that's not in our mapping
    custom_expr = exp.Anonymous(this="CUSTOM_FUNC", expressions=[exp.column("a")])
    result = parens_if_needed(custom_expr, "+", operand_type="left")

    # Unknown child expressions don't need parens
    assert result is custom_expr
    assert not isinstance(result, exp.Paren)


def test_nested_parentheses_not_double_wrapped():
    """Test that already parenthesized expressions aren't double-wrapped."""
    add_expr = exp.Add(this=exp.column("a"), expression=exp.column("b"))
    paren_expr = exp.Paren(this=add_expr)
    result = parens_if_needed(paren_expr, "*", operand_type="left")

    # Should not double-wrap; Paren is not in our binary operator mapping
    assert result is paren_expr
    assert not isinstance(result.this, exp.Paren)  # Not double-wrapped


def test_generated_sql_structure():
    """Test that wrapped expressions generate correct SQL structure."""
    # Create (a + b) * c
    add_expr = exp.Add(this=exp.column("a"), expression=exp.column("b"))
    wrapped = parens_if_needed(add_expr, "*", operand_type="left")

    # Should be wrapped and generate correct SQL
    assert isinstance(wrapped, exp.Paren)
    sql = wrapped.sql()
    assert sql == snapshot("(a + b)")


def test_associativity_sql_correctness():
    """Test that associativity generates mathematically correct SQL."""
    # Create b - c for use in a - (b - c)
    sub_expr = exp.Sub(this=exp.column("b"), expression=exp.column("c"))
    wrapped = parens_if_needed(sub_expr, "-", operand_type="right")

    # Should generate SQL with parentheses
    assert isinstance(wrapped, exp.Paren)
    sql = wrapped.sql()
    assert sql == snapshot("(b - c)")


def test_logical_precedence_sql():
    """Test logical operator precedence in generated SQL."""
    # Create b || c for use in a && (b || c)
    or_expr = exp.Or(this=exp.column("b"), expression=exp.column("c"))
    wrapped = parens_if_needed(or_expr, "&&", operand_type="left")

    # Should generate SQL with parentheses for correct precedence
    assert isinstance(wrapped, exp.Paren)
    sql = wrapped.sql()
    assert sql == snapshot("(b OR c)")


def test_unary_with_binary_expression_needs_parens():
    """Binary expressions should be wrapped when used with unary operators."""
    add_expr = exp.Add(this=exp.column("a"), expression=exp.column("b"))
    result = parens_if_needed(add_expr, "-", operand_type="unary")

    # Should be wrapped in parentheses
    assert isinstance(result, exp.Paren)
    assert result.this is add_expr


def test_unary_with_high_precedence_no_parens():
    """High precedence expressions don't need parens with unary operators."""
    # Test IS NULL
    is_expr = exp.Is(this=exp.column("a"), expression=exp.Null())
    result = parens_if_needed(is_expr, "!", operand_type="unary")
    assert result is is_expr
    assert not isinstance(result, exp.Paren)

    # Test IN expression
    in_expr = exp.In(this=exp.column("a"), expressions=[exp.Literal.number("1")])
    result = parens_if_needed(in_expr, "-", operand_type="unary")
    assert result is in_expr
    assert not isinstance(result, exp.Paren)

    # Test BETWEEN expression
    between_expr = exp.Between(
        this=exp.column("a"), low=exp.Literal.number("1"), high=exp.Literal.number("10")
    )
    result = parens_if_needed(between_expr, "+", operand_type="unary")
    assert result is between_expr
    assert not isinstance(result, exp.Paren)


def test_unary_with_literals_no_parens():
    """Literals and columns don't need parentheses with unary operators."""
    literal = exp.Literal.number("42")
    result = parens_if_needed(literal, "-", operand_type="unary")
    assert result is literal
    assert not isinstance(result, exp.Paren)

    column = exp.Column(this="test_col")
    result = parens_if_needed(column, "!", operand_type="unary")
    assert result is column
    assert not isinstance(result, exp.Paren)


def test_nested_unary_operators_need_parens():
    """Nested unary operators should be wrapped in parentheses."""
    # Test nested unary minus: -(- expr)
    inner_neg = exp.Neg(this=exp.Literal.number("5"))
    result = parens_if_needed(inner_neg, "-", operand_type="unary")
    assert isinstance(result, exp.Paren)
    assert result.this is inner_neg

    # Test nested unary NOT: !(! expr)
    inner_not = exp.Not(this=exp.Boolean(this=True))
    result = parens_if_needed(inner_not, "!", operand_type="unary")
    assert isinstance(result, exp.Paren)
    assert result.this is inner_not


def test_unary_operators_precedence():
    """Test various binary expressions with different unary operators."""
    test_cases = [
        (exp.Add(this=exp.column("a"), expression=exp.column("b")), "-"),
        (exp.Sub(this=exp.column("a"), expression=exp.column("b")), "+"),
        (exp.Mul(this=exp.column("a"), expression=exp.column("b")), "!"),
        (exp.Or(this=exp.column("a"), expression=exp.column("b")), "-"),
        (exp.And(this=exp.column("a"), expression=exp.column("b")), "!"),
    ]

    for binary_expr, unary_op in test_cases:
        result = parens_if_needed(binary_expr, unary_op, operand_type="unary")
        assert isinstance(result, exp.Paren)
        assert result.this is binary_expr


def test_unary_sql_generation():
    """Test that unary operators generate correct SQL with parentheses."""
    # Test -(a + b)
    add_expr = exp.Add(this=exp.column("a"), expression=exp.column("b"))
    wrapped = parens_if_needed(add_expr, "-", operand_type="unary")

    assert isinstance(wrapped, exp.Paren)
    sql = wrapped.sql()
    assert sql == snapshot("(a + b)")

    # Test !(a OR b)
    or_expr = exp.Or(this=exp.column("a"), expression=exp.column("b"))
    wrapped = parens_if_needed(or_expr, "!", operand_type="unary")

    assert isinstance(wrapped, exp.Paren)
    sql = wrapped.sql()
    assert sql == snapshot("(a OR b)")


def test_operand_type_validation():
    """Test that the API works with all operand types."""
    expr = exp.Add(this=exp.column("a"), expression=exp.column("b"))

    # Test left operand
    left_result = parens_if_needed(expr, "*", operand_type="left")
    assert isinstance(left_result, exp.Paren)

    # Test right operand
    right_result = parens_if_needed(expr, "*", operand_type="right")
    assert isinstance(right_result, exp.Paren)

    # Test unary operand
    unary_result = parens_if_needed(expr, "-", operand_type="unary")
    assert isinstance(unary_result, exp.Paren)


def test_different_operators_same_expression():
    """Test same expression with different parent operators."""
    expr = exp.Add(this=exp.column("a"), expression=exp.column("b"))

    # With higher precedence parent (no parens needed)
    result = parens_if_needed(expr, "^", operand_type="left")
    assert isinstance(result, exp.Paren)  # Lower precedence needs parens

    # With same precedence parent (no parens needed for left)
    result = parens_if_needed(expr, "+", operand_type="left")
    assert not isinstance(result, exp.Paren)

    # With unary operator (parens needed)
    result = parens_if_needed(expr, "-", operand_type="unary")
    assert isinstance(result, exp.Paren)


if __name__ == "__main__":
    pytest.main([__file__])
