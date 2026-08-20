"""Extract semantic placeholder references from SQL strings."""

from __future__ import annotations

import re
import sys
from typing import TYPE_CHECKING

if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias

from hex_sl_utils._vendor.sqlglot import exp, parse_one
from hex_sl_utils._vendor.sqlglot.errors import ParseError, TokenError
from hex_sl_utils.expr.expr_substitution import replace_dialect_agnostic_quotes
from hex_sl_utils.placeholder import PLACEHOLDER_KIND_SEMANTIC

if TYPE_CHECKING:
    from hex_sl_utils.dialect import Dialect

# Type alias for a reference to an item through an optional resource path.
QualifiedReference: TypeAlias = tuple[tuple[str, ...], str]


def get_placeholder_references(
    sql_expression: str,
    *,
    resource: str,
    dialect: Dialect,
    marker: str | None = None,
) -> list[tuple[str, str]]:
    """
    Extract resource-reference pairs for all ${...} references in a SQL string.

    Uses AST-based parsing for accuracy (correctly ignores placeholders in string
    literals and comments), with fallback to regex for unparseable SQL.

    For placeholders that use ${marker.{name}} or don't include a qualifier,
    the provided `resource` string will be used.

    Args:
        sql_expression: The SQL expression string to analyze
        resource: The resource identifier to use for placeholders
            without a qualifier or with the configured marker.
        dialect: The dialect to use for parsing.
        marker: An optional qualifier that represents the current resource.

    Returns:
        A list of (resource, item_name) tuples for each placeholder found.
        Order is not guaranteed.

    Examples:
        >>> refs = get_placeholder_references(
        ...     "${RESERVED.col1} + ${other.col2}",
        ...     "my_resource",
        ...     dialect = DuckDb,
        ...     marker="RESERVED",
        ... )
        >>> refs
        [("my_resource", "col1"), ("other", "col2")]

        >>> refs = get_placeholder_references(
        ...     "${foo} + ${RESERVED.bar}",
        ...     "my_resource",
        ...     dialect = DuckDb,
        ...     marker="RESERVED",
        ... )
        >>> refs
        [("my_resource", "foo"), ("my_resource", "bar")]

        >>> refs = get_placeholder_references(
        ...     "${other.foo} + ${RESERVED.bar}",
        ...     "my_resource",
        ...     dialect = DuckDb,
        ...     marker="RESERVED",
        ... )
        >>> refs
        [("other", "foo"), ("my_resource", "bar")]
    """
    sqlglot_dialect = dialect.sqlglot_dialect()

    # Normalize $[...] dialect-agnostic quotes before parsing so they don't
    # interfere with tokenization ($ is now treated as a special token)
    normalized_sql = replace_dialect_agnostic_quotes(sql_expression, dialect=dialect)
    try:
        parsed = parse_one(normalized_sql, dialect=sqlglot_dialect)
    except (ParseError, TokenError):
        return _get_placeholder_references_regex(sql_expression, resource, marker)

    references: list[tuple[str, str]] = []

    for placeholder in parsed.find_all(exp.Placeholder):
        # Only process semantic placeholders (${...} style, not {{...}})
        if placeholder.args.get("kind") != PLACEHOLDER_KIND_SEMANTIC:
            continue

        name = str(placeholder.name)

        # Handle ${marker}
        if marker is not None and name == marker:
            # Reference to current resource but not a specific dimension/measure
            continue

        # Handle ${marker.foo} format
        if marker is not None and name.startswith(f"{marker}."):
            item_name = name[len(marker) + 1 :]
            references.append((resource, item_name))

        # Handle ${other.foo} format
        elif "." in name:
            parsed_resource, item = name.split(".", 1)
            references.append((parsed_resource, item))

        # Handle bare ${foo} format
        else:
            references.append((resource, name))

    return references


def _get_placeholder_references_regex(
    sql_expression: str,
    resource: str,
    marker: str | None = None,
) -> list[tuple[str, str]]:
    """
    Extract (resource, item_name) tuples for all ${...} references using regex.

    This is the fallback implementation used when AST parsing fails.
    """
    references: list[tuple[str, str]] = []

    def process_placeholder(match: re.Match[str]) -> str:
        placeholder = match.group("placeholder")

        # Remove whitespace from placeholder
        placeholder = placeholder.replace(" ", "")

        # Handle ${marker}
        if marker is not None and placeholder == marker:
            # Reference to current resource but not a specific dimension/measure
            return ""

        # Handle ${marker.foo} format
        if marker is not None and placeholder.startswith(f"{marker}."):
            item_name = placeholder[len(marker) + 1 :]
            references.append((resource, item_name))

        # Handle ${other.foo} format
        elif "." in placeholder:
            parsed_resource, item = placeholder.split(".", 1)
            references.append((parsed_resource, item))

        # Handle bare ${foo} format
        else:
            references.append((resource, placeholder))

        # Return value unused, but required by re.sub
        return ""

    # Process all ${...} placeholders
    re.sub(r"\$\{(?P<placeholder>[^}]+)\}", process_placeholder, sql_expression)

    return references
