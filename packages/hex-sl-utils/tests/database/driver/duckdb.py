"""In-process DuckDB execution driver."""

from __future__ import annotations

import duckdb
import polars as pl

from database.driver.base import SqlDriver
from database.driver.query import RenderedQuery
from hex_sl_utils.placeholder import PlaceholderStyle


class DuckDBDriver(SqlDriver):
    dialect_name = "duckdb"
    placeholder_style = PlaceholderStyle.DOLLAR_NAMED

    def __init__(self) -> None:
        self.connection = duckdb.connect(":memory:")
        self.connection.sql("SET timezone = 'Asia/Tokyo'")

    def execute_rendered(self, query: RenderedQuery) -> pl.DataFrame:
        """Execute the query against the in-memory DuckDB connection."""
        if not isinstance(query.parameters, dict):
            msg = "DuckDB requires named parameters"
            raise TypeError(msg)
        return self.connection.sql(query.sql, params=query.parameters).pl()

    def close(self) -> None:
        self.connection.close()
