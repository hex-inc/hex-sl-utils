"""Credentialed Snowflake execution driver."""

from __future__ import annotations

from typing import Any

from snowflake.connector import connect  # type: ignore[reportMissingImports]

from database.driver.connection import get_env_var
from database.driver.polars_read_database import PolarsReadDatabaseDriver
from hex_sl_utils.placeholder import PlaceholderStyle


class SnowflakeDriver(PolarsReadDatabaseDriver):
    dialect_name = "snowflake"
    placeholder_style = PlaceholderStyle.PYFORMAT

    def __init__(self) -> None:
        driver_name = "snowflake"
        self._connection = connect(
            account=get_env_var("TEST_SNOWFLAKE_ACC", driver_name),
            user=get_env_var("TEST_SNOWFLAKE_USERNAME", driver_name),
            private_key=get_env_var("TEST_SNOWFLAKE_PRIVATE_KEY", driver_name),
            database=get_env_var("TEST_SNOWFLAKE_DB", driver_name),
            warehouse=get_env_var("TEST_SNOWFLAKE_WH", driver_name),
            role=get_env_var("TEST_SNOWFLAKE_ROLE", driver_name),
        )

    @property
    def params_name(self) -> str:
        return "params"

    def connection(self) -> Any:
        return self._connection

    def close(self) -> None:
        if not self._connection.is_closed():
            self._connection.close()
