"""Base contract and result normalization for test-only SQL drivers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from types import TracebackType
from typing import Optional

import polars as pl
from typing_extensions import Self

from database.driver.query import ExecutableQuery, RenderedQuery, render_query
from hex_sl_utils.datatype import DataType
from hex_sl_utils.dialect import Dialect
from hex_sl_utils.placeholder import PlaceholderStyle


class SqlDriver(ABC):
    """Execute a self-contained query in one database or warehouse target."""

    dialect_name: str
    placeholder_style: PlaceholderStyle

    @property
    def dialect(self) -> Dialect:
        """Return the utility dialect used to render this driver's SQL."""
        return Dialect.from_name(self.dialect_name)

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        self.close()

    def execute(self, query: ExecutableQuery, timezone: str = "UTC") -> pl.DataFrame:
        """Render, execute, and normalize one complete query."""
        rendered = render_query(query, self.dialect, self.placeholder_style)
        result = self.execute_rendered(rendered)
        return self.normalize_result(result, query.result_types, timezone)

    @abstractmethod
    def execute_rendered(self, query: RenderedQuery) -> pl.DataFrame:
        """Execute SQL that has already been rendered for this driver."""

    def normalize_result(
        self,
        result: pl.DataFrame,
        result_types: Mapping[str, DataType],
        timezone: str,
    ) -> pl.DataFrame:
        """Normalize timezone-aware result columns to the test timezone."""
        columns: list[pl.Series] = []
        for column in result.get_columns():
            expected_type = result_types.get(column.name)
            if expected_type != DataType.TIMESTAMPTZ or not isinstance(
                column.dtype, pl.Datetime
            ):
                columns.append(column)
            elif column.dtype.time_zone is None:
                columns.append(
                    column.dt.replace_time_zone("UTC").dt.convert_time_zone(timezone)
                )
            else:
                columns.append(column.dt.convert_time_zone(timezone))
        return pl.DataFrame(columns)

    def close(self) -> None:
        """Release resources held by the driver."""
