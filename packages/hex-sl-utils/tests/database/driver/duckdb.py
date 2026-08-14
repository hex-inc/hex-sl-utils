from __future__ import annotations

import duckdb
import polars as pl
from typing import TYPE_CHECKING, Any
from pathlib import Path

from hex_sl.dialect.base import HexSLDialect
from hex_sl.dialect.utils.placeholder import PlaceholderStyle
from . import SqlDriver

if TYPE_CHECKING:
    from hex_sl.project.dataset import Dataset


class DuckDBDriver(SqlDriver):
    def __init__(self) -> None:
        self.dialect = HexSLDialect.from_name("duckdb")
        self.conn = duckdb.connect(":memory:")
        self._register_parquet_files()

        # Set timezone
        self.conn.sql("SET timezone = 'Asia/Tokyo'")

    def _register_parquet_files(self) -> None:
        # Compute the base path relative to this file
        current_file = Path(__file__)
        base_path = current_file.parent.parent / "project_definitions" / "data"

        for database_path in base_path.iterdir():
            if database_path.is_dir():
                self.conn.sql(f"CREATE SCHEMA IF NOT EXISTS {database_path.name}")
                for file_path in database_path.glob("*.parquet"):
                    table_name = f"{database_path.name}.{file_path.stem}"
                    self.conn.sql(
                        f"CREATE TABLE {table_name} AS SELECT * FROM read_parquet('{file_path}')"
                    )

    def evaluate_dataset(
        self, dataset: Dataset, parameters: dict[str, Any] = None, timezone: str = "UTC"
    ) -> pl.DataFrame:
        """
        Evaluate the given dataset's sql query using DuckDB and return the results
        as a Polars DataFrame.

        Args:
            dataset (Dataset): The dataset to evaluate.
            timezone (str): The timezone to use for the evaluation.

        Returns:
            pl.DataFrame: The evaluation results as a Polars DataFrame.
        """

        sql, config = dataset.sql_placeholders(
            PlaceholderStyle.DOLLAR_NAMED, dialect=self.dialect
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

        result = self.conn.sql(sql, params=parameters).pl()

        return self.convert_timezones(result, dataset.dimensions_list, timezone)

    def __del__(self):
        self.conn.close()
