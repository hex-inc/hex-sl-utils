"""Microsoft SQL Server execution driver."""

from __future__ import annotations

import polars as pl
import pymssql

from database.driver.base import SqlDriver
from database.driver.query import RenderedQuery
from hex_sl_utils.placeholder import PlaceholderStyle


class MSSQLDriver(SqlDriver):
    dialect_name = "mssql"
    placeholder_style = PlaceholderStyle.PYFORMAT

    def __init__(self) -> None:
        server = "localhost"
        database = "master"
        username = "sa"
        password = "yourStrong(!)Password"

        self.connection = pymssql.connect(
            server=server,
            user=username,
            password=password,
            database=database,
            as_dict=True,
            port="1433",
        )
        with self.connection.cursor() as cursor:
            cursor.execute("USE [hex-sl-testing]")

    def execute_rendered(self, query: RenderedQuery) -> pl.DataFrame:
        """Execute one SQL Server query."""
        if not isinstance(query.parameters, dict):
            msg = "SQL Server requires named parameters"
            raise TypeError(msg)
        with self.connection.cursor() as cursor:
            if query.parameters:
                cursor.execute(query.sql, query.parameters)
            else:
                cursor.execute(query.sql)
            rows = cursor.fetchall()
        return pl.DataFrame(data=rows, orient="row", infer_schema_length=100_000)

    def close(self) -> None:
        self.connection.close()
