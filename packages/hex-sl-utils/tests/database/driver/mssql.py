from __future__ import annotations


import polars as pl
from typing import TYPE_CHECKING, Any

from hex_sl.dialect.base import HexSLDialect
from hex_sl.dialect.utils.placeholder import PlaceholderStyle
from . import SqlDriver


if TYPE_CHECKING:
    from hex_sl.project.dataset import Dataset


class MSSQLDriver(SqlDriver):
    def __init__(self):
        import pymssql

        # Connection parameters
        server = "localhost"
        database = "master"
        username = "sa"
        password = "yourStrong(!)Password"

        # Connect to the database
        self.connection = pymssql.connect(
            server=server,
            user=username,
            password=password,
            database=database,
            as_dict=True,
            port=1433,
        )
        with self.connection.cursor() as cursor:
            cursor.execute("USE [hex-sl-testing]")

        self.dialect = HexSLDialect.from_name("mssql")

    def evaluate_dataset(
        self, dataset: Dataset, parameters: dict[str, Any] = None, timezone: str = "UTC"
    ) -> pl.DataFrame:
        sql, config = dataset.sql_placeholders(
            PlaceholderStyle.PYFORMAT, dialect=self.dialect
        )
        parameters = (
            {
                name: value
                for name, value in parameters.items()
                if name in config.used_parameters
            }
            if parameters
            else {}
        )

        with self.connection.cursor() as cursor:
            cursor.execute(sql, parameters)
            rows = cursor.fetchall()

        result = pl.DataFrame(data=rows, orient="row", infer_schema_length=100000)
        return self.convert_timezones(result, dataset.dimensions_list, timezone)

    def __del__(self):
        if hasattr(self, "connection"):
            self.connection.close()
