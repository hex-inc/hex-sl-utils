# Register the custom dialect
from hex_sl._vendor.sqlglot.dialects.dialect import Dialect

from .bigquery import HexSlBigQuerySqlGlotDialect
from .clickhouse import HexSlClickHouseSqlGlotDialect
from .duckdb import HexSlDuckDBSqlGlotDialect
from .mssql import HexSlMSSQLSqlGlotDialect
from .mysql import HexSlMySQLSqlGlotDialect
from .postgres import HexSlPostgresSqlGlotDialect
from .redshift import HexSlRedshiftSqlGlotDialect
from .snowflake import HexSlSnowflakeSqlGlotDialect
from .spark import HexSlDatabricksSqlGlotDialect
from .trino import HexSlTrinoSqlGlotDialect

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
