# mypy: disable-error-code="no-untyped-call"
"""Extract semantic placeholder references from SQL strings."""

from __future__ import annotations

import re

from hex_sl._vendor.sqlglot import exp, parse_one
from hex_sl._vendor.sqlglot.errors import ParseError, TokenError
from hex_sl.dialect.utils.placeholder import PLACEHOLDER_KIND_SEMANTIC
from hex_sl.expr import replace_dialect_agnostic_quotes


def get_placeholder_references(
    sql_expression: str, this_dataset: str, dialect: str
) -> list[tuple[str, str]]:
    """
    Extract (dataset, item_name) tuples for all ${...} references in a SQL string.

    Uses AST-based parsing for accuracy (correctly ignores placeholders in string
    literals and comments), with fallback to regex for unparseable SQL.

    For placeholders that use ${DATASET.{name}} or don't include a dataset component,
    the provided this_dataset string will be used.

    Args:
        sql_expression: The SQL expression string to analyze
        this_dataset: The dataset name to use for ${DATASET} placeholders or
                     placeholders without a dataset component
        dialect: The SQLGlot dialect name to use for parsing

    Returns:
        A list of (dataset, item_name) tuples for each placeholder found.
        Order is not guaranteed.

    Examples:
        >>> refs = get_placeholder_references(
        ...     "${DATASET.col1} + ${other.col2}", "my_dataset", "duckdb"
        ... )
        >>> refs
        [("my_dataset", "col1"), ("other", "col2")]

        >>> refs = get_placeholder_references(
        ...     "${foo} + ${DATASET.bar}", "my_dataset", "duckdb"
        ... )
        >>> refs
        [("my_dataset", "foo"), ("my_dataset", "bar")]

        >>> refs = get_placeholder_references(
        ...     "${other.foo} + ${DATASET.bar}", "my_dataset", "duckdb"
        ... )
        >>> refs
        [("other", "foo"), ("my_dataset", "bar")]
    """
    # Normalize $[...] dialect-agnostic quotes before parsing so they don't
    # interfere with tokenization ($ is now treated as a special token)
    normalized_sql = replace_dialect_agnostic_quotes(sql_expression, dialect)
    try:
        parsed = parse_one(normalized_sql, dialect=dialect)
    except (ParseError, TokenError):
        return _get_placeholder_references_regex(sql_expression, this_dataset)

    references: list[tuple[str, str]] = []

    for placeholder in parsed.find_all(exp.Placeholder):
        # Only process semantic placeholders (${...} style, not {{...}})
        if placeholder.args.get("kind") != PLACEHOLDER_KIND_SEMANTIC:
            continue

        name = str(placeholder.name)

        # Handle ${DATASET}
        if name == "DATASET":
            # Reference to dataset table but not a specific dimension/measure
            continue

        # Handle ${DATASET.foo} format
        if name.startswith("DATASET."):
            item_name = name[len("DATASET.") :]
            references.append((this_dataset, item_name))

        # Handle ${other.foo} format
        elif "." in name:
            dataset, item = name.split(".", 1)
            references.append((dataset, item))

        # Handle bare ${foo} format
        else:
            references.append((this_dataset, name))

    return references


def _get_placeholder_references_regex(
    sql_expression: str, this_dataset: str
) -> list[tuple[str, str]]:
    """
    Extract (dataset, item_name) tuples for all ${...} references using regex.

    This is the fallback implementation used when AST parsing fails.
    """
    references: list[tuple[str, str]] = []

    def process_placeholder(match: re.Match[str]) -> str:
        placeholder = match.group("placeholder")

        # Remove whitespace from placeholder
        placeholder = placeholder.replace(" ", "")

        # Handle ${DATASET}
        if placeholder == "DATASET":
            # Reference to dataset table but not a specific dimension/measure
            return ""

        # Handle ${DATASET.foo} format
        if placeholder.startswith("DATASET."):
            item_name = placeholder[len("DATASET.") :]
            references.append((this_dataset, item_name))

        # Handle ${other.foo} format
        elif "." in placeholder:
            dataset, item = placeholder.split(".", 1)
            references.append((dataset, item))

        # Handle bare ${foo} format
        else:
            references.append((this_dataset, placeholder))

        # Return value unused, but required by re.sub
        return ""

    # Process all ${...} placeholders
    re.sub(r"\$\{(?P<placeholder>[^}]+)\}", process_placeholder, sql_expression)

    return references
