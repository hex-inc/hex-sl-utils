"""Tests for Trino dialect SQL parsing edge cases."""

from hex_sl_utils._vendor.sqlglot import exp, parse_one


def test_trino_cast_qdigest_parameterized_type():
    """
    Regression test for NOVA-4350: CAST to qdigest(bigint) should parse on Trino.

    Athena supports parameterized types like qdigest(bigint) and tdigest(double)
    in CAST expressions. The vendored sqlglot Trino dialect that we use for Athena
    doesn't recognize qdigest as a type keyword, so SUPPORTS_USER_DEFINED_TYPES
    must be enabled to allow parsing these types.
    """
    sql = "CAST(ttfb AS qdigest(bigint))"
    parsed = parse_one(sql, dialect="hex-sl-trino")
    assert isinstance(parsed, exp.Cast)

    result = parsed.sql(dialect="hex-sl-trino")
    assert result == "CAST(ttfb AS qdigest(BIGINT))"
