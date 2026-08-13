# Register the custom dialect
from hex_sl_utils._vendor.sqlglot.dialects.dialect import Dialect
from hex_sl_utils.dialect.bigquery import HexSlBigQuerySqlGlotDialect
from hex_sl_utils.dialect.clickhouse import HexSlClickHouseSqlGlotDialect
from hex_sl_utils.dialect.duckdb import HexSlDuckDBSqlGlotDialect
from hex_sl_utils.dialect.mssql import HexSlMSSQLSqlGlotDialect
from hex_sl_utils.dialect.mysql import HexSlMySQLSqlGlotDialect
from hex_sl_utils.dialect.postgres import HexSlPostgresSqlGlotDialect
from hex_sl_utils.dialect.redshift import HexSlRedshiftSqlGlotDialect
from hex_sl_utils.dialect.snowflake import HexSlSnowflakeSqlGlotDialect
from hex_sl_utils.dialect.spark import HexSlDatabricksSqlGlotDialect
from hex_sl_utils.dialect.trino import HexSlTrinoSqlGlotDialect

# Register our custom dialects with sqlglot
Dialect.classes[HexSlTrinoSqlGlotDialect.dialect_name()] = (
    # Athena
    HexSlTrinoSqlGlotDialect
)

Dialect.classes[HexSlBigQuerySqlGlotDialect.dialect_name()] = (
    # BigQuery
    HexSlBigQuerySqlGlotDialect
)

Dialect.classes[HexSlClickHouseSqlGlotDialect.dialect_name()] = (
    # ClickHouse
    HexSlClickHouseSqlGlotDialect
)

Dialect.classes[HexSlDatabricksSqlGlotDialect.dialect_name()] = (
    # Databricks
    HexSlDatabricksSqlGlotDialect
)

Dialect.classes[HexSlDuckDBSqlGlotDialect.dialect_name()] = (
    # DuckDB
    HexSlDuckDBSqlGlotDialect
)

Dialect.classes[HexSlMSSQLSqlGlotDialect.dialect_name()] = (
    # MSSQL
    HexSlMSSQLSqlGlotDialect
)

Dialect.classes[HexSlMySQLSqlGlotDialect.dialect_name()] = (
    # MySQL
    HexSlMySQLSqlGlotDialect
)

Dialect.classes[HexSlPostgresSqlGlotDialect.dialect_name()] = (
    # Postgres
    HexSlPostgresSqlGlotDialect
)

Dialect.classes[HexSlRedshiftSqlGlotDialect.dialect_name()] = (
    # Redshift
    HexSlRedshiftSqlGlotDialect
)

Dialect.classes[HexSlSnowflakeSqlGlotDialect.dialect_name()] = (
    # Snowflake
    HexSlSnowflakeSqlGlotDialect
)
