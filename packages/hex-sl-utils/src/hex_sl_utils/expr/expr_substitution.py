from hex_sl_utils._vendor.sqlglot import exp


def _needs_parens_for_substitution(expr: exp.Expression) -> bool:
    """
    Determine if an expression needs parentheses when substituted as a placeholder.

    Only binary operations and similar expressions that could have operator
    precedence issues when substituted into larger expressions need parentheses.

    Args:
        expr: The SQLGlot expression to check

    Returns:
        True if the expression should be wrapped in parentheses when substituted
    """
    # Binary and unary operations may need parens
    # to avoid operator precedence issues like a + b * c vs (a + b) * c
    if isinstance(expr, (exp.Binary, exp.Unary)):
        return True

    # Concat expressions need parens because they are transformed to
    # the || binary operator in some dialects during SQL generation
    if isinstance(expr, exp.Concat):  # noqa: SIM103
        return True

    return False
