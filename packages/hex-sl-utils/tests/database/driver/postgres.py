from __future__ import annotations
from typing import Any


from hex_sl.dialect.base import HexSLDialect
from hex_sl.dialect.utils.placeholder import PlaceholderStyle
from tests.driver.polars_read_database import PolarsReadDatabaseDriver


class PostgresDriver(PolarsReadDatabaseDriver):
    def __init__(self):
        from sqlalchemy import create_engine

        self._engine = create_engine(
            "postgresql://postgres:postgres@localhost:5437/hex_sl_testing"
        )
        self._dialect = HexSLDialect.from_name("postgres")
        self._placeholder_style = PlaceholderStyle.COLON_NAMED

    def connection(self) -> Any:
        return self._engine.connect()

    @property
    def placeholder_style(self) -> PlaceholderStyle:
        return self._placeholder_style

    @property
    def dialect(self) -> HexSLDialect:
        return self._dialect

    def execute_options(self, parameters: dict[str, Any]) -> dict[str, Any]:
        return parameters

    def __del__(self):
        if hasattr(self, "_engine"):
            try:
                self._engine.dispose()
            except Exception:  # noqa: BLE001
                pass
