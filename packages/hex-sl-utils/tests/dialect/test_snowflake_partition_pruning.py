import pytest
from hex_sl.dialect.snowflake import HexSLSnowflake
from hex_sl.project.dataset import Dataset
from hex_sl.calc.parser import parse_calc_expression
from hex_sl.expr import ExpressionContext
from hex_sl.schema import Schema
from hex_sl.datatype import DataType


class TestSnowflakePartitionPruning:
    """Test that HexSL generates partition-pruning-friendly SQL for Snowflake.

    Ensures that date/timestamp operations avoid functions that prevent partition pruning:
    - DATE_FROM_PARTS()
    - TIMESTAMP_FROM_PARTS()
    - TIMESTAMP_NTZ_FROM_DATE_TIME()

    For more details see: https://community.snowflake.com/s/article/Pruning-does-not-occur-when-functions-DATE-FROM-PARTS-TIMESTAMP-FROM-PARTS-and-TIMESTAMP-NTZ-FROM-DATE-TIME-are-used
    """

    @pytest.fixture
    def dialect(self):
        return HexSLSnowflake()

    def _get_generated_sql_from_calc(
        self, dialect, calc_expr: str, table_name: str = "HEX_SL_TESTING.tpch.lineitem"
    ) -> str:
        """Helper to compile a calc expression and get the generated SQL."""
        # Create a simple schema with the columns we need
        schema = Schema(
            name="test_schema",
            types={
                "l_shipdate": DataType.DATE,
                "l_commitdate": DataType.TIMESTAMP,
                "l_receiptdate": DataType.TIMESTAMPTZ,
            },
        )

        # Parse and compile the calc expression
        parsed_expr = parse_calc_expression(calc_expr)
        compiled_expr = dialect.compile_expression(
            parsed_expr,
            ExpressionContext.WHERE,
            schema,
            "UTC",
            parameters={},
        )

        # Generate SQL with the expression in a WHERE clause
        dataset_sql = f"SELECT COUNT(*) as cnt FROM {table_name} WHERE {compiled_expr.expression.sql(dialect=dialect.sqlglot_dialect())}"
        dataset = Dataset(name="test_sql_generation", sql=dataset_sql)
        return dataset.base_sql(dialect=dialect)

    def _assert_no_partition_blocking_functions(self, sql: str, test_name: str):
        """Assert that SQL doesn't contain functions that block partition pruning."""
        blocking_functions = [
            "DATE_FROM_PARTS(",
            "TIMESTAMP_FROM_PARTS(",
            "TIMESTAMP_NTZ_FROM_DATE_TIME(",
        ]

        for func in blocking_functions:
            assert func not in sql.upper(), (
                f"{test_name}: Generated SQL contains partition-blocking function {func}. "
                f"This prevents partition pruning in Snowflake.\nGenerated SQL: {sql}"
            )

    def test_date_literal_sql_generation(self, dialect):
        """Test that date literal filtering generates partition-friendly SQL."""
        # Use hex-sl date literal syntax: d"YYYY-MM-DD"
        calc_expr = 'l_shipdate > d"2005-01-01"'

        generated_sql = self._get_generated_sql_from_calc(dialect, calc_expr)
        self._assert_no_partition_blocking_functions(
            generated_sql, "Date literal filtering"
        )

    def test_timestamp_literal_sql_generation(self, dialect):
        """Test that timestamp literal filtering generates partition-friendly SQL."""
        # Use hex-sl timestamp literal syntax: t"YYYY-MM-DDTHH:MM:SS"
        calc_expr = 'l_commitdate > t"2005-01-01T12:30:45"'

        generated_sql = self._get_generated_sql_from_calc(dialect, calc_expr)
        self._assert_no_partition_blocking_functions(
            generated_sql, "Timestamp literal filtering"
        )

    def test_timestamptz_literal_sql_generation(self, dialect):
        """Test that timezone-aware timestamp filtering generates partition-friendly SQL."""
        # Use hex-sl toDatetime function with timezone parameter to create timestamptz
        calc_expr = 'l_receiptdate > toDatetime("2000-01-01T12:30:45", "UTC")'

        generated_sql = self._get_generated_sql_from_calc(dialect, calc_expr)
        self._assert_no_partition_blocking_functions(
            generated_sql, "Timezone-aware timestamp filtering"
        )

    def test_date_range_query_sql_generation(self, dialect):
        """Test that date range queries generate partition-friendly SQL."""
        # Use hex-sl BETWEEN operator with date literals
        calc_expr = 'l_shipdate >= d"2005-01-01" && l_shipdate <= d"2010-12-31"'

        generated_sql = self._get_generated_sql_from_calc(dialect, calc_expr)
        self._assert_no_partition_blocking_functions(generated_sql, "Date range query")

    @pytest.mark.parametrize(
        "calc_expr,case_name",
        [
            ('l_shipdate == d"2005-01-01"', "Date equality"),
            ('l_receiptdate >= t"2005-01-01T12:00:00"', "Timestamp comparison"),
            ("l_shipdate > today()", "Date arithmetic with today()"),
        ],
    )
    def test_date_construction_avoids_blocking_functions(
        self, dialect, calc_expr, case_name
    ):
        """Test that date construction from parts avoids partition-blocking functions."""
        generated_sql = self._get_generated_sql_from_calc(dialect, calc_expr)
        self._assert_no_partition_blocking_functions(generated_sql, case_name)
