"""Tests for placeholder analysis utilities."""

import pytest

from hex_sl_utils._vendor.sqlglot import exp, parse_one
from hex_sl_utils.dialect import Dialect
from hex_sl_utils.placeholder.placeholder_analysis import (
    get_placeholder_name,
    get_semantic_placeholders,
    is_semantic_placeholder,
    parse_placeholder_reference,
)


@pytest.fixture
def duckdb_dialect() -> str:
    return Dialect.from_name("duckdb").sqlglot_dialect()


class TestGetPlaceholderName:
    def test_semantic_placeholder_string_name(self, duckdb_dialect: str) -> None:
        """Semantic placeholders store name as string."""
        ast = parse_one("${foo}", dialect=duckdb_dialect)
        placeholders = list(ast.find_all(exp.Placeholder))
        assert len(placeholders) == 1
        assert get_placeholder_name(placeholders[0]) == "foo"

    def test_semantic_placeholder_dotted_name(self, duckdb_dialect: str) -> None:
        """Dotted semantic placeholders preserve the full name."""
        ast = parse_one("${dataset.column}", dialect=duckdb_dialect)
        placeholders = list(ast.find_all(exp.Placeholder))
        assert len(placeholders) == 1
        assert get_placeholder_name(placeholders[0]) == "dataset.column"

    def test_query_param_placeholder_identifier_name(self, duckdb_dialect: str) -> None:
        """Query param placeholders store name as Identifier."""
        ast = parse_one("{{foo}}", dialect=duckdb_dialect)
        placeholders = list(ast.find_all(exp.Placeholder))
        assert len(placeholders) == 1
        assert get_placeholder_name(placeholders[0]) == "foo"


class TestIsSemanticPlaceholder:
    def test_semantic_placeholder(self, duckdb_dialect: str) -> None:
        """${...} placeholders are semantic."""
        ast = parse_one("${foo}", dialect=duckdb_dialect)
        placeholders = list(ast.find_all(exp.Placeholder))
        assert len(placeholders) == 1
        assert is_semantic_placeholder(placeholders[0]) is True

    def test_query_param_not_semantic(self, duckdb_dialect: str) -> None:
        """{{...}} placeholders are not semantic."""
        ast = parse_one("{{foo}}", dialect=duckdb_dialect)
        placeholders = list(ast.find_all(exp.Placeholder))
        assert len(placeholders) == 1
        assert is_semantic_placeholder(placeholders[0]) is False


class TestGetSemanticPlaceholders:
    def test_finds_semantic_placeholders(self, duckdb_dialect: str) -> None:
        """Should find all ${...} placeholders."""
        ast = parse_one("${a} + ${b} + ${c}", dialect=duckdb_dialect)
        placeholders = get_semantic_placeholders(ast)
        assert len(placeholders) == 3
        names = {get_placeholder_name(p) for p in placeholders}
        assert names == {"a", "b", "c"}

    def test_excludes_query_param_placeholders(self, duckdb_dialect: str) -> None:
        """Should not include {{...}} placeholders."""
        ast = parse_one("${semantic} + {{query_param}}", dialect=duckdb_dialect)
        placeholders = get_semantic_placeholders(ast)
        assert len(placeholders) == 1
        assert get_placeholder_name(placeholders[0]) == "semantic"

    def test_empty_when_no_semantic(self, duckdb_dialect: str) -> None:
        """Should return empty list if no semantic placeholders."""
        ast = parse_one("{{a}} + {{b}}", dialect=duckdb_dialect)
        placeholders = get_semantic_placeholders(ast)
        assert len(placeholders) == 0


class TestParsePlaceholderReference:
    def test_bare_name(self) -> None:
        """Bare name uses this_dataset."""
        dataset, item = parse_placeholder_reference("foo", resource="my_resource")
        assert dataset == "my_resource"
        assert item == "foo"

    def test_dataset_placeholder(self) -> None:
        """The marker resolves against the current dataset."""
        resource, item = parse_placeholder_reference(
            "ABC.foo", resource="my_resource", marker="ABC"
        )
        assert resource == "my_resource"
        assert item == "foo"

    def test_no_implicit_marker(self) -> None:
        """A qualifier is retained when no marker is supplied."""
        resource, item = parse_placeholder_reference("ABC.foo", resource="my_resource")
        assert resource == "ABC"
        assert item == "foo"

    def test_custom_marker(self) -> None:
        """A consumer can choose its own current-resource marker."""
        resource, item = parse_placeholder_reference(
            "ABC.foo", resource="my_resource", marker="ABC"
        )
        assert resource == "my_resource"
        assert item == "foo"

    def test_explicit_qualifier(self) -> None:
        """An explicit resource reference is retained."""
        resource, item = parse_placeholder_reference(
            "other.foo", resource="my_resource"
        )
        assert resource == "other"
        assert item == "foo"

    def test_whitespace_stripped(self) -> None:
        """Whitespace in placeholder names is removed."""
        resource, item = parse_placeholder_reference(" foo ", resource="my_resource")
        assert resource == "my_resource"
        assert item == "foo"


@pytest.mark.parametrize("dialect_name", Dialect.all_dialects)
def test_placeholder_analysis_all_dialects(dialect_name: str) -> None:
    """Semantic placeholder analysis works with every registered dialect."""
    dialect = Dialect.from_name(dialect_name).sqlglot_dialect()
    ast = parse_one("${item} + {{query_parameter}}", dialect=dialect)
    placeholders = get_semantic_placeholders(ast)

    assert [get_placeholder_name(placeholder) for placeholder in placeholders] == [
        "item"
    ]
