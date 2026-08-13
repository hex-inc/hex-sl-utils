from hex_sl._vendor.sqlglot import exp, parse_one
from hex_sl._vendor.sqlglot.dialects.dialect import map_date_part
from inline_snapshot import snapshot


class TestNova4471UnquotedDateParts:
    """Regression tests for NOVA-4471: unquoted date parts must not crash."""

    def test_date_trunc_unquoted(self):
        result = parse_one("SELECT DATE_TRUNC(day, col) FROM t", dialect="snowflake")
        assert result.sql(dialect="snowflake") == snapshot(
            "SELECT DATE_TRUNC('DAY', col) FROM t"
        )

    def test_date_trunc_quoted(self):
        result = parse_one("SELECT DATE_TRUNC('day', col) FROM t", dialect="snowflake")
        assert result.sql(dialect="snowflake") == snapshot(
            "SELECT DATE_TRUNC('DAY', col) FROM t"
        )

    def test_date_part_unquoted(self):
        result = parse_one("SELECT DATE_PART(year, col) FROM t", dialect="snowflake")
        assert result.sql(dialect="snowflake") == snapshot(
            "SELECT DATE_PART(year, col) FROM t"
        )

    def test_to_timestamp_column_arg(self):
        result = parse_one("SELECT TO_TIMESTAMP(col) FROM t", dialect="snowflake")
        assert result.sql(dialect="snowflake") == snapshot(
            "SELECT TO_TIMESTAMP(col) FROM t"
        )

    def test_map_date_part_multi_part_column_passthrough(self):
        col = exp.Column(this=exp.to_identifier("col"), table=exp.to_identifier("t"))
        assert map_date_part(col) is col

    def test_text_resolves_non_leaf_expression_args(self):
        """text() resolves any Expression arg via .name, not just Identifier/Literal/Var."""
        wrapper = exp.Expression(this=exp.Column(this=exp.to_identifier("d")))
        assert wrapper.name == "d"
        assert map_date_part(wrapper) == exp.var("DAY")
