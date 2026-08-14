from __future__ import annotations
from typing import Any

from hex_sl.dialect.base import HexSLDialect
from hex_sl.dialect.utils.placeholder import PlaceholderStyle
from tests.driver import get_env_var
from tests.driver.polars_read_database import PolarsReadDatabaseDriver
import redshift_connector


class RedshiftDriver(PolarsReadDatabaseDriver):
    def __init__(self):
        self._connection = None
        self._dialect = HexSLDialect.from_name("redshift")
        self._placeholder_style = PlaceholderStyle.FORMAT

    @property
    def params_name(self) -> str:
        return "args"

    def connection(self) -> Any:
        driver_name = "redshift"
        connection_parameters = {
            "host": get_env_var("TEST_REDSHIFT_ENDPOINT", driver_name),
            "port": get_env_var("TEST_REDSHIFT_PORT", driver_name),
            "user": get_env_var("TEST_REDSHIFT_USERNAME", driver_name),
            "database": get_env_var("TEST_REDSHIFT_DB", driver_name),
            "password": get_env_var("TEST_REDSHIFT_PASSWORD", driver_name),
        }

        self._connection = redshift_connector.connect(
            **connection_parameters,
        )
        return self._connection

    @property
    def placeholder_style(self) -> PlaceholderStyle:
        return self._placeholder_style

    @property
    def dialect(self) -> HexSLDialect:
        return self._dialect

    def __del__(self):
        if hasattr(self, "_connection"):
            self._connection.close()
