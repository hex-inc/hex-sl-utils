"""PostgreSQL execution driver."""

from __future__ import annotations

from typing import Any

from sqlalchemy import create_engine

from database.driver.polars_read_database import PolarsReadDatabaseDriver
from hex_sl_utils.placeholder import PlaceholderStyle


class PostgresDriver(PolarsReadDatabaseDriver):
    dialect_name = "postgres"
    placeholder_style = PlaceholderStyle.COLON_NAMED

    def __init__(self) -> None:
        self._engine: Any = create_engine(
            "postgresql://postgres:postgres@localhost:5437/hex_sl_testing"
        )

    def connection(self) -> Any:
        return self._engine.connect()

    def close(self) -> None:
        self._engine.dispose()
