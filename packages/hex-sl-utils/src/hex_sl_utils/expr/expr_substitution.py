import re

from hex_sl._vendor.sqlglot import to_identifier

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


def replace_dialect_agnostic_quotes(sql_expression: str, dialect: str) -> str:
    """
    Replace $[identifier] with dialect-specific quoted identifiers.

    This is the dialect-agnostic quoting syntax that gets converted to the
    appropriate quote characters for each SQL dialect (e.g., double quotes
    for Snowflake, backticks for MySQL).

    Args:
        sql_expression: The SQL expression string containing $[...] syntax.
        dialect: The target SQL dialect name.

    Returns:
        The SQL expression with $[identifier] replaced by dialect-specific quotes.
    """

    def replace_quotes(match: re.Match[str]) -> str:
        identifier = match.group(1)
        return to_identifier(identifier, quoted=True).sql(dialect=dialect)

    return re.sub(r"\$\[([^\]]+)\]", replace_quotes, sql_expression)
