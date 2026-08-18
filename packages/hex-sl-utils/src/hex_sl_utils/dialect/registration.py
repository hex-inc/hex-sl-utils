# Register the custom dialect
from hex_sl_utils._vendor.sqlglot.dialects.dialect import Dialect
from hex_sl_utils.dialect.bigquery import BigQuerySqlGlotOverride
from hex_sl_utils.dialect.clickhouse import ClickHouseSqlGlotOverride
from hex_sl_utils.dialect.duckdb import DuckDBSqlGlotOverride
from hex_sl_utils.dialect.mssql import MSSQLSqlGlotOverride
from hex_sl_utils.dialect.mysql import MySQLSqlGlotOverride
from hex_sl_utils.dialect.postgres import PostgresSqlGlotOverride
from hex_sl_utils.dialect.redshift import RedshiftSqlGlotOverride
from hex_sl_utils.dialect.snowflake import SnowflakeSqlGlotOverride
from hex_sl_utils.dialect.spark import SparkSqlGlotOverride
from hex_sl_utils.dialect.trino import TrinoSqlGlotOverride

# Register our custom dialects with sqlglot
Dialect.classes[TrinoSqlGlotOverride.dialect_name()] = (
    # Athena
    TrinoSqlGlotOverride
)

Dialect.classes[BigQuerySqlGlotOverride.dialect_name()] = (
    # BigQuery
    BigQuerySqlGlotOverride
)

Dialect.classes[ClickHouseSqlGlotOverride.dialect_name()] = (
    # ClickHouse
    ClickHouseSqlGlotOverride
)

Dialect.classes[SparkSqlGlotOverride.dialect_name()] = (
    # Databricks
    SparkSqlGlotOverride
)

Dialect.classes[DuckDBSqlGlotOverride.dialect_name()] = (
    # DuckDB
    DuckDBSqlGlotOverride
)

Dialect.classes[MSSQLSqlGlotOverride.dialect_name()] = (
    # MSSQL
    MSSQLSqlGlotOverride
)

Dialect.classes[MySQLSqlGlotOverride.dialect_name()] = (
    # MySQL
    MySQLSqlGlotOverride
)

Dialect.classes[PostgresSqlGlotOverride.dialect_name()] = (
    # Postgres
    PostgresSqlGlotOverride
)

Dialect.classes[RedshiftSqlGlotOverride.dialect_name()] = (
    # Redshift
    RedshiftSqlGlotOverride
)

Dialect.classes[SnowflakeSqlGlotOverride.dialect_name()] = (
    # Snowflake
    SnowflakeSqlGlotOverride
)
