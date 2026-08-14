from __future__ import annotations

from typing import Any

from snowflake.connector.connection import SnowflakeConnection

from hex_sl.dialect.base import HexSLDialect
from hex_sl.dialect.utils.placeholder import PlaceholderStyle
from tests.driver import get_env_var
from tests.driver.polars_read_database import PolarsReadDatabaseDriver
from snowflake.connector import connect


class SnowflakeDriver(PolarsReadDatabaseDriver):
    def __init__(self):
        driver_name = "snowflake"

        connection_parameters = {
            "account": get_env_var("TEST_SNOWFLAKE_ACC", driver_name),
            "user": get_env_var("TEST_SNOWFLAKE_USERNAME", driver_name),
            "private_key": get_env_var("TEST_SNOWFLAKE_PRIVATE_KEY", driver_name),
            "database": get_env_var("TEST_SNOWFLAKE_DB", driver_name),
            "warehouse": get_env_var("TEST_SNOWFLAKE_WH", driver_name),
            "role": get_env_var("TEST_SNOWFLAKE_ROLE", driver_name),
        }

        self._connection = connect(**connection_parameters)
        self._dialect = HexSLDialect.from_name("snowflake")
        self._placeholder_style = PlaceholderStyle.PYFORMAT

    @property
    def params_name(self) -> str:
        return "params"

    def connection(self) -> SnowflakeConnection:
        return self._connection

    @property
    def placeholder_style(self) -> PlaceholderStyle:
        return self._placeholder_style

    @property
    def dialect(self) -> HexSLDialect:
        return self._dialect

    def execute_ddl(self, sql: str) -> Any:
        """
        Execute a DDL statement that doesn't return a result set.

        Args:
            sql: The DDL SQL statement to execute

        Returns:
            The result from the cursor execution (e.g., status message)
        """
        cursor = self._connection.cursor()
        try:
            result = cursor.execute(sql)
            if sql.strip().upper().startswith("CALL"):
                return cursor.fetchone()[0] if cursor.rowcount > 0 else None
            return result
        finally:
            cursor.close()

    def create_schema_if_not_exists(self, database: str, schema: str) -> None:
        """Create schema if it doesn't exist."""
        sql = f'CREATE SCHEMA IF NOT EXISTS "{database}"."{schema}"'
        self.execute_ddl(sql)

    def drop_semantic_view_if_exists(
        self, database: str, schema: str, view_name: str
    ) -> None:
        """Drop semantic view if it exists."""
        sql = f'DROP SEMANTIC VIEW IF EXISTS "{database}"."{schema}"."{view_name}"'
        self.execute_ddl(sql)

    def __del__(self):
        if (
            hasattr(self, "_connection")
            and self._connection is not None
            and not self._connection.is_closed()
        ):
            self._connection.close()
