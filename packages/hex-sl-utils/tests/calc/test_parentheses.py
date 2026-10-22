"""Tests for the unified parentheses system for calc language binary and unary expressions."""

from typing import cast

import pytest
from inline_snapshot import snapshot

from hex_sl_utils._vendor.sqlglot import exp, parse_one
from hex_sl_utils.calc import CalcExpr, parse_calc_expression
from hex_sl_utils.calc.operators import CalcOp, UnaryOp
from hex_sl_utils.calc.parentheses import (
    OPERATOR_PRECEDENCE,
    parens_if_needed,
)
from hex_sl_utils.datatype import DataType
from hex_sl_utils.dialect import Dialect
from hex_sl_utils.expr import ExpressionContext, ExpressionKind, TypedSelectExpression


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


def test_atomic_operands_do_not_need_parentheses():
    """Atomic operands (literals and column references) need no extra grouping.

    Other non-binary SQLGlot expressions, including Not, In, Between, and
    AtTimeZone, can need parentheses when embedded in another operation.
    """
    literal = exp.Literal.number(42)
    column = exp.Column(this="test_col")

    for expr in [literal, column]:
        for op in OPERATOR_PRECEDENCE:
            result = parens_if_needed(expr, cast(CalcOp, op), operand_type="left")
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


def test_arithmetic_operands_follow_associativity():
    """Preserve right-operand grouping even for associative arithmetic operators.

    Addition is mathematically associative, but floating-point rounding can make
    a + (b + c) differ from (a + b) + c. Keep the right operand grouped; the left
    operand already follows SQL's left-associative parsing.
    """
    add_expr = exp.Add(this=exp.column("a"), expression=exp.column("b"))

    left = parens_if_needed(add_expr, "+", operand_type="left")
    right = parens_if_needed(add_expr, "+", operand_type="right")

    assert left is add_expr
    assert isinstance(right, exp.Paren)
    assert right.this is add_expr


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


def test_function_operands_do_not_need_parentheses():
    """Named function calls delimit their arguments and form a single operand.

    This exemption is specific to function-call syntax. An unrecognized operator
    can bind to the surrounding expression, so it must be grouped instead.
    """
    custom_expr = exp.Anonymous(this="CUSTOM_FUNC", expressions=[exp.column("a")])
    result = parens_if_needed(custom_expr, "+", operand_type="left")

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
    test_cases: list[tuple[exp.Expression, UnaryOp]] = [
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


@pytest.mark.parametrize(
    "dialect_name",
    [
        "clickhouse",
        "duckdb",
        "mssql",
        "mysql",
        "postgres",
        "redshift",
        "snowflake",
        "spark",
        "trino",
    ],
)
@pytest.mark.parametrize(
    ("operator", "symbol"),
    [(exp.Add, "+"), (exp.Sub, "-"), (exp.Mul, "*")],
)
def test_division_preserves_divisor_grouping(dialect_name, operator, symbol):
    dialect = Dialect.from_name(dialect_name)
    dividend = TypedSelectExpression.from_sqlglot(
        exp.column("a"), DataType.NUMBER, ExpressionKind.COLUMN
    )
    divisor = TypedSelectExpression.from_sqlglot(
        operator(this=exp.column("b"), expression=exp.column("c")),
        DataType.NUMBER,
        ExpressionKind.COLUMN,
    )

    result = dialect.build_division(dividend, divisor)
    sql = result.expression.sql(dialect=dialect.sqlglot_dialect())
    dividend_sql = (
        dialect.cast_to_float(dividend).expression.sql(
            dialect=dialect.sqlglot_dialect()
        )
        if dialect.truncates_on_integer_division()
        else "a"
    )

    assert sql == f"{dividend_sql} / (b {symbol} c)"


@pytest.mark.parametrize("operand_type", ["left", "right"])
@pytest.mark.parametrize(
    ("operator", "symbol"),
    [
        (exp.EQ, "="),
        (exp.NEQ, "!="),
        (exp.LT, "<"),
        (exp.LTE, "<="),
        (exp.GT, ">"),
        (exp.GTE, ">="),
    ],
)
def test_nested_comparisons_preserve_grouping(operator, symbol, operand_type):
    operand = operator(this=exp.column("a"), expression=exp.column("b"))

    result = parens_if_needed(operand, symbol, operand_type=operand_type)

    assert isinstance(result, exp.Paren)
    assert result.this is operand


@pytest.mark.parametrize("operand_type", ["left", "right"])
@pytest.mark.parametrize(
    "operand",
    [
        exp.Not(this=exp.column("a")),
        exp.Is(this=exp.column("a"), expression=exp.Null()),
        exp.In(this=exp.column("a"), expressions=[exp.Literal.number(1)]),
        exp.Between(
            this=exp.column("a"), low=exp.Literal.number(1), high=exp.Literal.number(2)
        ),
        exp.Like(this=exp.column("a"), expression=exp.Literal.string("a%")),
        exp.BitwiseAnd(this=exp.column("a"), expression=exp.column("b")),
    ],
)
def test_unmapped_operators_preserve_grouping(operand, operand_type):
    result = parens_if_needed(operand, "=", operand_type=operand_type)

    assert isinstance(result, exp.Paren)
    assert result.this is operand


@pytest.mark.parametrize(
    ("parent_op", "operator"),
    [("-", exp.Add), ("+", exp.Sub), ("*", exp.Div), ("/", exp.Mul), ("%", exp.Mul)],
)
def test_right_arithmetic_operands_preserve_grouping(parent_op, operator):
    operand = operator(this=exp.column("a"), expression=exp.column("b"))

    result = parens_if_needed(operand, parent_op, operand_type="right")

    assert isinstance(result, exp.Paren)
    assert result.this is operand


@pytest.mark.parametrize("operand_type", ["left", "right"])
@pytest.mark.parametrize("parent_op", ["&&", "||"])
def test_not_operands_do_not_need_parentheses_in_logical_operations(
    parent_op, operand_type
):
    operand = exp.Not(this=exp.column("a"))

    result = parens_if_needed(operand, parent_op, operand_type=operand_type)

    assert result is operand


@pytest.mark.parametrize(
    ("parent_op", "child_operator", "child_sql"),
    [("-", exp.Add, "b + c"), ("/", exp.Mul, "b * c"), ("%", exp.Mul, "b * c")],
)
def test_same_precedence_right_operand_preserves_grouping(
    parent_op, child_operator, child_sql
):
    child = child_operator(this=exp.column("b"), expression=exp.column("c"))

    result = parens_if_needed(child, parent_op, operand_type="right")

    assert result.sql() == f"({child_sql})"
    assert parens_if_needed(child, parent_op, operand_type="left") is child
    assert parens_if_needed(result, parent_op, operand_type="right") is result


@pytest.mark.parametrize(
    "dialect_name", [name for name in Dialect.all_dialects if name != "bigquery"]
)
@pytest.mark.parametrize(
    ("source", "grouped_operand"),
    [
        ("10 - (2 + 3)", "(2 + 3)"),
        ("12 / (2 * 3)", "(2 * 3)"),
        ("20 % (2 * 3)", "(2 * 3)"),
    ],
)
def test_compiler_preserves_right_operand_grouping(
    dialect_name, source, grouped_operand
):
    dialect = Dialect.from_name(dialect_name)

    result = dialect.compile_calc_expr(
        parse_calc_expression(source),
        context=ExpressionContext.PROJECTION,
        columns={},
        timezone="UTC",
        parameters={},
    )

    arithmetic = result.expression
    if isinstance(arithmetic, exp.Case):
        arithmetic = arithmetic.args["default"]

    assert grouped_operand in arithmetic.sql(dialect=dialect.sqlglot_dialect())


@pytest.mark.parametrize(
    ("divisor_sql", "divisor_type"),
    [("6 & 3", exp.BitwiseAnd), ("7 // 2", exp.IntDiv)],
)
def test_compiler_preserves_sql_expression_divisor_grouping(divisor_sql, divisor_type):
    dialect = Dialect.from_name("duckdb")
    calc = CalcExpr.model_validate(
        {
            "binary": "/",
            "lhs": {"number": 12},
            "rhs": {"sql": divisor_sql, "data_type": DataType.NUMBER},
        }
    )

    result = dialect.compile_calc_expr(
        calc,
        context=ExpressionContext.PROJECTION,
        columns={},
        timezone="UTC",
        parameters={},
    )
    sql = result.expression.sql(dialect=dialect.sqlglot_dialect())
    parsed = parse_one(sql, dialect=dialect.sqlglot_dialect())
    division = parsed.args["default"]

    assert isinstance(division, exp.Div)
    assert isinstance(division.right, exp.Paren)
    assert isinstance(division.right.this, divisor_type)


@pytest.mark.parametrize("dialect_name", Dialect.all_dialects)
@pytest.mark.parametrize("operand_type", ["left", "right"])
@pytest.mark.parametrize(
    "child_operator", [exp.EQ, exp.NEQ, exp.LT, exp.LTE, exp.GT, exp.GTE]
)
@pytest.mark.parametrize(
    ("parent_operator", "symbol"),
    [
        (exp.EQ, "="),
        (exp.NEQ, "!="),
        (exp.LT, "<"),
        (exp.LTE, "<="),
        (exp.GT, ">"),
        (exp.GTE, ">="),
    ],
)
def test_comparison_grouping_round_trips(
    dialect_name, operand_type, child_operator, parent_operator, symbol
):
    dialect = Dialect.from_name(dialect_name)
    child = child_operator(this=exp.column("a"), expression=exp.column("b"))
    operand = parens_if_needed(child, symbol, operand_type=operand_type)
    left, right = (
        (operand, exp.column("c"))
        if operand_type == "left"
        else (exp.column("c"), operand)
    )
    expression = parent_operator(this=left, expression=right)

    sql = expression.sql(dialect=dialect.sqlglot_dialect())
    parsed = parse_one(sql, dialect=dialect.sqlglot_dialect())

    expected = expression.transform(
        lambda node: node.this if isinstance(node, exp.Paren) else node
    )
    actual = parsed.transform(
        lambda node: node.this if isinstance(node, exp.Paren) else node
    )
    assert actual == expected


@pytest.mark.parametrize("dialect_name", Dialect.all_dialects)
@pytest.mark.parametrize("operand_type", ["left", "right"])
@pytest.mark.parametrize(
    "predicate_sql",
    ["NOT (x > 0)", "x IS NULL", "x IN (1, 2)", "x BETWEEN 1 AND 2", "x LIKE 'a%'"],
)
def test_predicate_operand_grouping_round_trips(
    dialect_name, operand_type, predicate_sql
):
    dialect = Dialect.from_name(dialect_name)
    predicate = parse_one(predicate_sql, dialect=dialect.sqlglot_dialect())
    operand = parens_if_needed(predicate, "=", operand_type=operand_type)
    left, right = (
        (operand, exp.column("flag"))
        if operand_type == "left"
        else (exp.column("flag"), operand)
    )
    expression = exp.EQ(this=left, expression=right)

    sql = expression.sql(dialect=dialect.sqlglot_dialect())
    parsed = parse_one(sql, dialect=dialect.sqlglot_dialect())

    expected = expression.transform(
        lambda node: node.this if isinstance(node, exp.Paren) else node
    )
    actual = parsed.transform(
        lambda node: node.this if isinstance(node, exp.Paren) else node
    )
    assert actual == expected
