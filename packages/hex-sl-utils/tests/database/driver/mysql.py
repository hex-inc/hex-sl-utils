from __future__ import annotations


import polars as pl
from typing import TYPE_CHECKING, Any

from hex_sl.dialect.base import HexSLDialect
from hex_sl.dialect.utils.placeholder import PlaceholderStyle
from . import SqlDriver

if TYPE_CHECKING:
    from hex_sl.project.dataset import Dataset


class MySqlDriver(SqlDriver):
    def __init__(self):
        import pymysql.cursors

        # Connect to the database
        self.connection = pymysql.connect(
            host="localhost",
            user="mysql",
            password="mysql",
            cursorclass=pymysql.cursors.DictCursor,
        )

        self.dialect = HexSLDialect.from_name("mysql")

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
            else None
        )

        with self.connection.cursor() as cursor:
            cursor.execute(sql, args=parameters)
            rows = cursor.fetchall()
            cols = [d[0] for d in cursor.description]

        result = pl.DataFrame(
            data=rows, schema=cols, orient="row", infer_schema_length=100000
        )
        return self.convert_timezones(result, dataset.dimensions_list, timezone)

    def __del__(self):
        if hasattr(self, "connection"):
            self.connection.close()
