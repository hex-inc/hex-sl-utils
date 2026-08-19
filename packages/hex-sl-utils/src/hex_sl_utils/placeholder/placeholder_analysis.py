"""Utilities for analyzing placeholders in parsed SQL ASTs."""

from __future__ import annotations

from hex_sl_utils._vendor.sqlglot import exp
from hex_sl_utils.exception import UserFacingError


def get_placeholder_name(placeholder: exp.Placeholder) -> str:
    """
    Extract the name from a Placeholder node.

    For semantic placeholders (${...}), the name is stored as a string.
    For query param placeholders ({{...}}), the name is an Identifier.
    """
    this = placeholder.this
    if isinstance(this, str):
        return this
    elif isinstance(this, exp.Identifier):
        return this.name
    else:
        return str(this)


def is_semantic_placeholder(placeholder: exp.Placeholder) -> bool:
    """Check if a placeholder is a semantic placeholder (${...} style)."""
    return placeholder.args.get("kind") == "semantic"


def get_semantic_placeholders(expr: exp.Expression) -> list[exp.Placeholder]:
    """
    Find all semantic placeholders (${...}) in an expression.

    Excludes query parameter placeholders ({{...}}).
    """
    return [p for p in expr.find_all(exp.Placeholder) if is_semantic_placeholder(p)]


def parse_placeholder_reference(
    placeholder_name: str,
    *,
    resource: str,
    marker: str | None = None,
) -> tuple[str, str]:
    """
    Parse a placeholder name into a (resource, item_name) tuple.

    Handles these formats:
    - "foo" -> (resource, "foo")
    - "RESERVED.foo" -> (resource, "foo") when marker="RESERVED"
    - "other.foo" -> ("other", "foo")

    Args:
        placeholder_name: The placeholder name (e.g., "foo", "RESERVED.foo", "other.foo")
        resource: The current resource identifier.
        marker: An optional qualifier that represents the current resource.

    Returns:
        Tuple of (resource, item_name)

    Raises:
        UserFacingError: If the placeholder name results in an empty resource
            reference or item name.
    """
    placeholder_name = placeholder_name.replace(" ", "")

    if marker is not None and placeholder_name.startswith(f"{marker}."):
        item_name = placeholder_name[len(marker) + 1 :]
        if not item_name:
            msg = f"Empty item name in placeholder: ${{{placeholder_name}}}"
            raise UserFacingError(msg)
        return (resource, item_name)

    if "." in placeholder_name:
        parsed_resource, item = placeholder_name.split(".", 1)
        if not parsed_resource:
            msg = f"Empty resource name in placeholder: ${{{placeholder_name}}}"
            raise UserFacingError(msg)
        if not item:
            msg = f"Empty item name in placeholder: ${{{placeholder_name}}}"
            raise UserFacingError(msg)
        return (parsed_resource, item)

    if not placeholder_name:
        msg = "Empty placeholder name"
        raise UserFacingError(msg)
    return (resource, placeholder_name)
