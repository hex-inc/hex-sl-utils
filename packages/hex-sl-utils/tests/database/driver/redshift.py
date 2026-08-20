"""Credentialed Redshift execution driver."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import polars as pl
import redshift_connector  # type: ignore[reportMissingImports]

from database.driver.connection import get_env_port, get_env_var
from database.driver.polars_read_database import PolarsReadDatabaseDriver
from hex_sl_utils.datatype import DataType
from hex_sl_utils.placeholder import PlaceholderStyle


class RedshiftDriver(PolarsReadDatabaseDriver):
    dialect_name = "redshift"
    placeholder_style = PlaceholderStyle.FORMAT

    def __init__(self) -> None:
        self._connection: Any | None = None

    @property
    def params_name(self) -> str:
        return "args"

    def connection(self) -> Any:
        if self._connection is None:
            driver_name = "redshift"
            self._connection = redshift_connector.connect(
                host=get_env_var("TEST_REDSHIFT_ENDPOINT", driver_name),
                port=get_env_port("TEST_REDSHIFT_PORT", driver_name),
                user=get_env_var("TEST_REDSHIFT_USERNAME", driver_name),
                database=get_env_var("TEST_REDSHIFT_DB", driver_name),
                password=get_env_var("TEST_REDSHIFT_PASSWORD", driver_name),
            )
        return self._connection

    def normalize_result(
        self,
        result: pl.DataFrame,
        result_types: Mapping[str, DataType],
        timezone: str,
    ) -> pl.DataFrame:
        """Match Redshift's lower-cased result-column behavior."""
        normalized = result.rename(
            {column: column.lower() for column in result.columns}
        )
        return super().normalize_result(normalized, result_types, timezone)

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
