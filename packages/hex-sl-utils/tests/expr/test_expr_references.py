"""Tests for semantic placeholder reference extraction."""

from hex_sl.expr import get_placeholder_references

DIALECT = "hex-sl-duckdb"


def test_get_placeholder_references():
    # Test DATASET placeholders (both formats)
    assert get_placeholder_references(
        "${DATASET}.col1 + ${DATASET.col2}", "my_dataset", DIALECT
    ) == [
        ("my_dataset", "col2"),
    ]

    # Test bare placeholders
    assert get_placeholder_references("${foo} + ${bar}", "my_dataset", DIALECT) == [
        ("my_dataset", "foo"),
        ("my_dataset", "bar"),
    ]

    # Test cross-dataset references (both formats)
    assert get_placeholder_references(
        "${orders.total} + ${customers.id}", "my_dataset", DIALECT
    ) == [
        ("orders", "total"),
        ("customers", "id"),
    ]

    # Test mixed formats (order may vary between AST and regex, use set comparison)
    assert set(
        get_placeholder_references(
            "${DATASET}.col1 + ${other.col2} + ${third.col3} + ${DATASET.col4} + ${foo}",
            "my_dataset",
            DIALECT,
        )
    ) == {
        ("other", "col2"),
        ("third", "col3"),
        ("my_dataset", "col4"),
        ("my_dataset", "foo"),
    }

    # Test empty string
    assert get_placeholder_references("", "my_dataset", DIALECT) == []

    # Test string without placeholders
    assert (
        get_placeholder_references("SELECT * FROM table", "my_dataset", DIALECT) == []
    )

    # Test with whitespace around dots (AST parsing normalizes whitespace)
    assert get_placeholder_references(
        "${DATASET. col1} + ${other . col2}", "my_dataset", DIALECT
    ) == [
        ("my_dataset", "col1"),
        ("other", "col2"),
    ]


def test_get_placeholder_references_ast_ignores_string_literals():
    """AST-based extraction correctly ignores placeholders in string literals."""
    assert get_placeholder_references(
        "'${not_a_ref}' || ${real_ref}", "my_dataset", DIALECT
    ) == [("my_dataset", "real_ref")]


def test_get_placeholder_references_fallback_to_regex():
    """Unparseable SQL falls back to regex extraction."""
    # This is invalid SQL that can't be parsed as an expression
    refs = get_placeholder_references(
        "NOT VALID SQL ${fallback_var} HERE",
        "my_dataset",
        DIALECT,
    )
    # Should still extract via regex fallback
    assert refs == [("my_dataset", "fallback_var")]
