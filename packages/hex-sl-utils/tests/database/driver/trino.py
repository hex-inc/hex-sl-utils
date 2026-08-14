"""Trino execution driver."""

from __future__ import annotations

from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL

from database.driver.polars_read_database import PolarsReadDatabaseDriver
from hex_sl_utils.placeholder import PlaceholderStyle


class TrinoDriver(PolarsReadDatabaseDriver):
    dialect_name = "trino"
    placeholder_style = PlaceholderStyle.QMARK

    def __init__(self) -> None:
        self._engine: Any = create_engine(
            URL.create(
                drivername="trino",
                host="localhost",
                port=8093,
                database="hive",
                username="trino",
                query={"protocol": "http", "auth": "basic"},
            )
        )

    def connection(self) -> Any:
        return self._engine.connect()

    def close(self) -> None:
        self._engine.dispose()
