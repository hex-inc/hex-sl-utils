"""Tests for expression inspection utilities."""

from hex_sl_utils._vendor.sqlglot import parse_one
from hex_sl_utils.dialect import Dialect
from hex_sl_utils.expr import get_referenced_placeholders


def test_get_referenced_placeholders() -> None:
    dialect = Dialect.from_name("duckdb").sqlglot_dialect()
    expression = parse_one(
        "${semantic} + {{query_parameter}}",
        dialect=dialect,
    )

    assert get_referenced_placeholders(expression) == {
        "semantic",
        "query_parameter",
    }
