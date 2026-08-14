from __future__ import annotations
from typing import Any
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL

from hex_sl.dialect.base import HexSLDialect
from hex_sl.dialect.utils.placeholder import PlaceholderStyle
from tests.driver.polars_read_database import PolarsReadDatabaseDriver


class TrinoDriver(PolarsReadDatabaseDriver):
    def __init__(self):
        self._engine = create_engine(
            URL.create(
                drivername="trino",
                host="localhost",
                port=8093,
                database="hive",
                username="trino",
                query={
                    "protocol": "http",
                    "auth": "basic",
                },
            )
        )
        self._dialect = HexSLDialect.from_name("athena")
        self._placeholder_style = PlaceholderStyle.QMARK

    def connection(self) -> Any:
        return self._engine.connect()

    @property
    def placeholder_style(self) -> PlaceholderStyle:
        return self._placeholder_style

    @property
    def dialect(self) -> HexSLDialect:
        return self._dialect

    def __del__(self):
        if hasattr(self, "_engine"):
            self._engine.dispose()
