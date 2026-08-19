# mypy: disable-error-code="no-untyped-call"
"""
Utilities for analyzing placeholders in parsed SQL AST.
"""

from __future__ import annotations

from hex_sl_common.exceptions import UserFacingError

from hex_sl._vendor.sqlglot import exp


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
    placeholder_name: str, this_dataset: str
) -> tuple[str, str]:
    """
    Parse a placeholder name into (dataset, item_name) tuple.

    Handles these formats:
    - "foo" -> (this_dataset, "foo")
    - "DATASET.foo" -> (this_dataset, "foo")
    - "other.foo" -> ("other", "foo")

    Args:
        placeholder_name: The placeholder name (e.g., "foo", "DATASET.foo", "other.foo")
        this_dataset: The default dataset name to use for bare references

    Returns:
        Tuple of (dataset_name, item_name)

    Raises:
        UserFacingError: If the placeholder name results in empty dataset or item_name
    """
    placeholder_name = placeholder_name.replace(" ", "")

    if placeholder_name.startswith("DATASET."):
        item_name = placeholder_name[len("DATASET.") :]
        if not item_name:
            msg = f"Empty item name in placeholder: ${{{placeholder_name}}}"
            raise UserFacingError(msg)
        return (this_dataset, item_name)

    if "." in placeholder_name:
        dataset, item = placeholder_name.split(".", 1)
        if not dataset:
            msg = f"Empty dataset name in placeholder: ${{{placeholder_name}}}"
            raise UserFacingError(msg)
        if not item:
            msg = f"Empty item name in placeholder: ${{{placeholder_name}}}"
            raise UserFacingError(msg)
        return (dataset, item)

    if not placeholder_name:
        msg = "Empty placeholder name"
        raise UserFacingError(msg)
    return (this_dataset, placeholder_name)
