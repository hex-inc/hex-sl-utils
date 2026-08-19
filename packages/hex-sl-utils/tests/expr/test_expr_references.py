"""Tests for semantic placeholder reference extraction."""

from __future__ import annotations

import pytest

from hex_sl_utils.dialect import Dialect
from hex_sl_utils.expr import get_placeholder_references


@pytest.fixture
def dialect() -> Dialect:
    return Dialect.from_name("duckdb")


def test_get_placeholder_references(dialect: Dialect) -> None:
    # Test marker placeholders (both formats)
    assert get_placeholder_references(
        "${ABC}.col1 + ${ABC.col2}",
        resource="my_resource",
        dialect=dialect,
        marker="ABC",
    ) == [
        ("my_resource", "col2"),
    ]

    # Test bare placeholders
    assert get_placeholder_references(
        "${foo} + ${bar}", resource="my_resource", dialect=dialect
    ) == [
        ("my_resource", "foo"),
        ("my_resource", "bar"),
    ]

    # Test cross-dataset references (both formats)
    assert get_placeholder_references(
        "${orders.total} + ${customers.id}", resource="my_resource", dialect=dialect
    ) == [
        ("orders", "total"),
        ("customers", "id"),
    ]

    # Test mixed formats (order may vary between AST and regex, use set comparison)
    assert set(
        get_placeholder_references(
            "${ABC}.col1 + ${other.col2} + ${third.col3} + ${ABC.col4} + ${foo}",
            resource="my_resource",
            dialect=dialect,
            marker="ABC",
        )
    ) == {
        ("other", "col2"),
        ("third", "col3"),
        ("my_resource", "col4"),
        ("my_resource", "foo"),
    }

    # Test empty string
    assert get_placeholder_references("", resource="my_resource", dialect=dialect) == []

    # Test string without placeholders
    assert (
        get_placeholder_references(
            "SELECT * FROM table", resource="my_resource", dialect=dialect
        )
        == []
    )

    # Test with whitespace around dots (AST parsing normalizes whitespace)
    assert get_placeholder_references(
        "${ABC. col1} + ${other . col2}",
        resource="my_resource",
        dialect=dialect,
        marker="ABC",
    ) == [
        ("my_resource", "col1"),
        ("other", "col2"),
    ]


def test_get_placeholder_references_ast_ignores_string_literals(
    dialect: Dialect,
) -> None:
    """AST-based extraction correctly ignores placeholders in string literals."""
    assert get_placeholder_references(
        "'${not_a_ref}' || ${real_ref}", resource="my_resource", dialect=dialect
    ) == [("my_resource", "real_ref")]


def test_get_placeholder_references_fallback_to_regex(
    dialect: Dialect,
) -> None:
    """Unparseable SQL falls back to regex extraction."""
    # This is invalid SQL that can't be parsed as an expression
    refs = get_placeholder_references(
        "NOT VALID SQL ${fallback_var} HERE", resource="my_resource", dialect=dialect
    )
    # Should still extract via regex fallback
    assert refs == [("my_resource", "fallback_var")]


def test_get_placeholder_references_fallback_honors_marker(
    dialect: Dialect,
) -> None:
    """Regex fallback applies the optional marker semantics."""
    refs = get_placeholder_references(
        "NOT VALID SQL ${RESOURCE} ${RESOURCE.fallback_var} HERE",
        resource="my_resource",
        dialect=dialect,
        marker="RESOURCE",
    )
    assert refs == [("my_resource", "fallback_var")]


def test_get_placeholder_references_ignores_comments(
    dialect: Dialect,
) -> None:
    """AST extraction ignores placeholder-like text outside SQL expressions."""
    assert get_placeholder_references(
        "${active} -- ${commented}", resource="my_resource", dialect=dialect
    ) == [("my_resource", "active")]
    assert get_placeholder_references(
        "${active} /* ${commented} */ + ${other}",
        resource="my_resource",
        dialect=dialect,
    ) == [("my_resource", "active"), ("my_resource", "other")]


def test_get_placeholder_references_preserves_duplicates(
    dialect: Dialect,
) -> None:
    assert get_placeholder_references(
        "${a} + ${a} + ${a}", resource="my_resource", dialect=dialect
    ) == [
        ("my_resource", "a"),
        ("my_resource", "a"),
        ("my_resource", "a"),
    ]


def test_get_placeholder_references_excludes_non_item_placeholders(
    dialect: Dialect,
) -> None:
    assert (
        get_placeholder_references(
            "${ABC} AS t",
            resource="my_resource",
            dialect=dialect,
            marker="ABC",
        )
        == []
    )
    assert get_placeholder_references(
        "${semantic} + {{query_parameter}}", resource="my_resource", dialect=dialect
    ) == [("my_resource", "semantic")]


def test_get_placeholder_references_has_no_implicit_marker(
    dialect: Dialect,
) -> None:
    """ABC is an ordinary item or qualifier when no marker is supplied."""
    assert get_placeholder_references(
        "${ABC} + ${ABC.item}", resource="my_resource", dialect=dialect
    ) == [("my_resource", "ABC"), ("ABC", "item")]


def test_get_placeholder_references_accepts_custom_marker(
    dialect: Dialect,
) -> None:
    """A consumer can choose its own current-resource marker."""
    assert set(
        get_placeholder_references(
            "${ABC} + ${ABC.item} + ${OTHER.item}",
            resource="my_resource",
            dialect=dialect,
            marker="ABC",
        )
    ) == {("my_resource", "item"), ("OTHER", "item")}


def test_get_placeholder_references_handles_dialect_agnostic_quotes(
    dialect: Dialect,
) -> None:
    assert get_placeholder_references(
        "$[amount] + ${tax}", resource="my_resource", dialect=dialect
    ) == [("my_resource", "tax")]


@pytest.mark.parametrize("dialect_name", Dialect.all_dialects)
def test_get_placeholder_references_all_dialects(dialect_name: str) -> None:
    dialect = Dialect.from_name(dialect_name)
    assert set(
        get_placeholder_references(
            "${ABC.col1} + ${other.col2}",
            resource="my_resource",
            dialect=dialect,
            marker="ABC",
        )
    ) == {("my_resource", "col1"), ("other", "col2")}
