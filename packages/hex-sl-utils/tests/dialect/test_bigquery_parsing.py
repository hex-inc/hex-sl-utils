"""Tests for BigQuery dialect SQL parsing and round-trip."""

from inline_snapshot import snapshot

from hex_sl_utils._vendor.sqlglot import exp, parse_one


def test_bigquery_extract_format_parse_roundtrip():
    """
    Test parsing and round-tripping a BigQuery query with EXTRACT and FORMAT.

    This tests the reported issue where BigQuery queries with EXTRACT and
    CAST with FORMAT clause fail to parse.
    """
    sql = """select
    *,
    extract(DAYOFYEAR from created_at) as DAYOFYEAR,
    cast(created_at as string format('YYYY-MM')) as month_created
  from user_analytics_prod_ai_safe.projects_qualified"""

    # Parse with the hex-sl-bigquery dialect
    parsed = parse_one(sql, dialect="hex-sl-bigquery")

    # Round-trip back to SQL
    result = parsed.sql(dialect="hex-sl-bigquery", pretty=True)

    # Compare with snapshot
    assert result == snapshot(
        """\
SELECT
  *,
  EXTRACT(DAYOFYEAR FROM created_at) AS DAYOFYEAR,
  CAST(created_at AS STRING FORMAT 'YYYY-MM') AS month_created
FROM user_analytics_prod_ai_safe.projects_qualified\
"""
    )


def test_bigquery_format_syntaxes():
    """Test that both FORMAT 'string' and FORMAT('string') syntaxes are supported."""
    # Test FORMAT with parentheses
    sql_parens = "SELECT CAST(created_at AS STRING FORMAT('YYYY-MM')) as month_created"
    parsed_parens = parse_one(sql_parens, dialect="hex-sl-bigquery")
    assert isinstance(parsed_parens, exp.Select)

    # Test FORMAT without parentheses
    sql_no_parens = (
        "SELECT CAST(created_at AS STRING FORMAT 'YYYY-MM') as month_created"
    )
    parsed_no_parens = parse_one(sql_no_parens, dialect="hex-sl-bigquery")
    assert isinstance(parsed_no_parens, exp.Select)

    # Both should produce valid SQL when converted back
    result_parens = parsed_parens.sql(dialect="hex-sl-bigquery")
    result_no_parens = parsed_no_parens.sql(dialect="hex-sl-bigquery")

    # Should be able to re-parse both
    reparsed_parens = parse_one(result_parens, dialect="hex-sl-bigquery")
    reparsed_no_parens = parse_one(result_no_parens, dialect="hex-sl-bigquery")

    assert isinstance(reparsed_parens, exp.Select)
    assert isinstance(reparsed_no_parens, exp.Select)

    # Both syntaxes should produce semantically equivalent SQL
    # (they may differ in formatting but should have the same structure)
    # The generated SQL should always use the standard FORMAT 'string' syntax
    assert "FORMAT 'YYYY-MM'" in result_parens
    assert "FORMAT 'YYYY-MM'" in result_no_parens
