"""MySQL-dialect execution driver backed by the source MariaDB service."""

from __future__ import annotations

import polars as pl
import pymysql
import pymysql.cursors

from database.driver.base import SqlDriver
from database.driver.connection import get_local_port
from database.driver.query import RenderedQuery
from hex_sl_utils.placeholder import PlaceholderStyle


class MySqlDriver(SqlDriver):
    dialect_name = "mysql"
    placeholder_style = PlaceholderStyle.PYFORMAT

    def __init__(self) -> None:
        self.connection = pymysql.connect(
            host="127.0.0.1",
            port=get_local_port("mysql", 3306),
            user="mysql",
            password="mysql",
            cursorclass=pymysql.cursors.DictCursor,
        )

    def execute_rendered(self, query: RenderedQuery) -> pl.DataFrame:
        """Execute one MySQL-dialect query."""
        if not isinstance(query.parameters, dict):
            msg = "MySQL requires named parameters"
            raise TypeError(msg)
        with self.connection.cursor() as cursor:
            if query.parameters:
                cursor.execute(query.sql, args=query.parameters)
            else:
                cursor.execute(query.sql)
            rows = cursor.fetchall()
            cols = [d[0] for d in cursor.description]
        return pl.DataFrame(
            data=rows,
            schema=cols,
            orient="row",
            infer_schema_length=100_000,
        )

    def close(self) -> None:
        self.connection.close()
