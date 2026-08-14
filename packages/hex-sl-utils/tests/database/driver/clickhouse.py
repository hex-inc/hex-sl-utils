"""ClickHouse execution driver."""

from __future__ import annotations

import clickhouse_connect
import polars as pl

from database.driver.base import SqlDriver
from database.driver.query import RenderedQuery
from hex_sl_utils.placeholder import PlaceholderStyle


class ClickHouseDriver(SqlDriver):
    dialect_name = "clickhouse"
    placeholder_style = PlaceholderStyle.CLICKHOUSE

    def __init__(self) -> None:
        self.connection = clickhouse_connect.get_client(
            host="localhost", port=8123, username="default"
        )

    def execute_rendered(self, query: RenderedQuery) -> pl.DataFrame:
        """Execute one ClickHouse query and preserve date result types."""
        if not isinstance(query.parameters, dict):
            msg = "ClickHouse requires named parameters"
            raise TypeError(msg)
        pd_result = self.connection.query_df(
            query.sql,
            parameters=query.parameters,
            use_na_values=False,
            use_none=True,
            query_tz="UTC",
        )
        result = pl.from_pandas(pd_result)

        # The approach above converts ClickHouse Dates to Polars Datetimes;
        # fix this here by looking at the true types from ClickHouse.
        if any(isinstance(dtype, pl.Datetime) for dtype in result.dtypes):
            clickhouse_dtypes = self.connection.query(query.sql).column_types
            for col, dtype in zip(result.columns, clickhouse_dtypes, strict=True):
                if dtype.name in {"Date", "Nullable(Date)"}:
                    result = result.with_columns(pl.col(col).cast(pl.Date).alias(col))
        return result

    def close(self) -> None:
        self.connection.close()
