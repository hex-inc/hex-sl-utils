"""Tests for placeholder analysis utilities."""

import pytest
from hex_sl._vendor.sqlglot import exp, parse_one
from hex_sl.dialect.base import HexSLDialect
from hex_sl.dialect.utils.placeholder_analysis import (
    get_placeholder_name,
    get_semantic_placeholders,
    is_semantic_placeholder,
    parse_placeholder_reference,
)


@pytest.fixture
def duckdb_dialect() -> str:
    """Return the DuckDB dialect name for parsing."""
    return HexSLDialect.from_name("duckdb").sqlglot_dialect()


class TestGetPlaceholderName:
    """Tests for get_placeholder_name function."""

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
    """Tests for is_semantic_placeholder function."""

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
    """Tests for get_semantic_placeholders function."""

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
    """Tests for parse_placeholder_reference function."""

    def test_bare_name(self) -> None:
        """Bare name uses this_dataset."""
        dataset, item = parse_placeholder_reference("foo", "my_dataset")
        assert dataset == "my_dataset"
        assert item == "foo"

    def test_dataset_placeholder(self) -> None:
        """DATASET.name uses this_dataset."""
        dataset, item = parse_placeholder_reference("DATASET.foo", "my_dataset")
        assert dataset == "my_dataset"
        assert item == "foo"

    def test_explicit_dataset(self) -> None:
        """other.name uses explicit dataset."""
        dataset, item = parse_placeholder_reference("other.foo", "my_dataset")
        assert dataset == "other"
        assert item == "foo"

    def test_whitespace_stripped(self) -> None:
        """Whitespace in placeholder is removed."""
        dataset, item = parse_placeholder_reference(" foo ", "my_dataset")
        assert dataset == "my_dataset"
        assert item == "foo"
