"""
Parentheses handling for calc language SQL expression generation.

This module provides unified logic for determining when parentheses are needed
around subexpressions based on operator precedence and associativity rules
specific to the calc language.
"""

from __future__ import annotations

from typing import get_args

from hex_sl._vendor.sqlglot import exp
from hex_sl.calc.operators import CalcOp, OperandType, UnaryOp

# Define operator precedence (higher number = higher precedence)
# Based on the calc grammar.lark file
OPERATOR_PRECEDENCE = {
    "||": 1,  # Logical OR
    "&&": 2,  # Logical AND
    "=": 3,  # Equality
    "!=": 3,  # Inequality
    "<": 4,  # Relational
    "<=": 4,
    ">": 4,
    ">=": 4,
    "+": 5,  # Additive
    "-": 5,
    "*": 6,  # Multiplicative
    "/": 6,
    "%": 6,
    "^": 7,  # Power
    # Unary operators have highest precedence (implicit)
    "unary": 8,
}


def _needs_parens_binary(child_expr: exp.Expression, parent_op: str) -> bool:
    """Check if child expression needs parentheses based on operator precedence."""
    # Map sqlglot expression types to our operator strings
    expr_type_to_op: dict[type[exp.Expression], str] = {
        exp.Or: "||",
        exp.And: "&&",
        exp.EQ: "=",
        exp.NEQ: "!=",
        exp.LT: "<",
        exp.LTE: "<=",
        exp.GT: ">",
        exp.GTE: ">=",
        exp.Add: "+",
        exp.Sub: "-",
        exp.Mul: "*",
        exp.Div: "/",
        exp.Mod: "%",
        exp.Pow: "^",
    }

    child_op = expr_type_to_op.get(type(child_expr))
    if not child_op:
        # Not a binary operator, no parens needed
        return False

    parent_prec = OPERATOR_PRECEDENCE.get(parent_op, 0)
    child_prec = OPERATOR_PRECEDENCE.get(child_op, 0)

    # Need parentheses if child has lower precedence
    return child_prec < parent_prec


def _needs_parens_unary(expr: exp.Expression, unary_op: UnaryOp) -> bool:
    """
    Check if an expression needs parentheses when used as the operand
    of a unary operator.

    Unary operators have higher precedence than all binary operators, so we need
    parentheses when the operand is a binary expression to maintain the correct
    order of operations.

    However, some expressions like NOT IS NULL don't need parentheses because they
    have very high precedence and the result is unambiguous.
    """
    # Special cases that don't need parentheses
    if unary_op == "!" and isinstance(expr, (exp.Is, exp.In, exp.Between)):
        # IS NULL, IS NOT NULL, IN (...), BETWEEN x AND y have high precedence
        # and don't create ambiguity with NOT
        return False

    # All unary and binary operators need parentheses when used as operand
    # of unary operator
    return isinstance(expr, (exp.Unary, exp.Binary))


def parens_if_needed(
    expr: exp.Expression, parent_op: CalcOp, operand_type: OperandType
) -> exp.Expression:
    """
    Wrap expression in parentheses if needed based on precedence rules.

    Args:
        expr: The expression to potentially wrap
        parent_op: The calc language operator (BinaryOp for binary context,
                  UnaryOp for unary context)
        operand_type: The type of operand - "left", "right" for binary operators,
                     "unary" for unary operators

    Returns:
        The expression, possibly wrapped in parentheses
    """
    if operand_type == "unary":
        # Handle unary operator context
        # parent_op must be a UnaryOp in this context
        assert parent_op in get_args(UnaryOp), f"Invalid unary operator: {parent_op}"
        if _needs_parens_unary(expr, parent_op):  # type: ignore[arg-type]
            return exp.Paren(this=expr)
        return expr

    # Handle binary operator context
    if _needs_parens_binary(expr, parent_op):
        return exp.Paren(this=expr)

    # Special case for right operands of left-associative operators
    # with same precedence (e.g., a - (b - c) vs (a - b) - c)
    if operand_type == "right" and parent_op in ("-", "/", "%"):
        expr_type_to_op: dict[type[exp.Expression], str] = {
            exp.Sub: "-",
            exp.Div: "/",
            exp.Mod: "%",
        }
        child_op = expr_type_to_op.get(type(expr))
        if child_op and OPERATOR_PRECEDENCE.get(child_op) == OPERATOR_PRECEDENCE.get(
            parent_op
        ):
            return exp.Paren(this=expr)

    return expr


__all__ = [
    "OPERATOR_PRECEDENCE",
    "parens_if_needed",
]
