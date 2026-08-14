"""SQLAlchemy-compatible driver support using Polars result conversion."""

from __future__ import annotations

from typing import Any

import polars as pl

from database.driver.base import SqlDriver
from database.driver.query import RenderedQuery


class PolarsReadDatabaseDriver(SqlDriver):
    """Execute rendered SQL through Polars."""

    def connection(self) -> Any:
        """Return a connection compatible with Polars."""
        msg = "Concrete drivers must implement connection()"
        raise NotImplementedError(msg)

    @property
    def params_name(self) -> str:
        """Return the keyword expected by the DB-API implementation."""
        return "parameters"

    def execute_options(self, parameters: Any) -> dict[str, Any]:
        """Return Polars execution options for native parameters."""
        return {self.params_name: parameters}

    def execute_rendered(self, query: RenderedQuery) -> pl.DataFrame:
        """Execute one rendered query and return its Polars result."""
        return pl.read_database(
            query.sql,
            connection=self.connection(),
            execute_options=self.execute_options(query.parameters),
            infer_schema_length=100_000,
        )
