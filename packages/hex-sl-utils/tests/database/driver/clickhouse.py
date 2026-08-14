from __future__ import annotations


import polars as pl
from typing import TYPE_CHECKING, Any

from hex_sl.dialect.base import HexSLDialect
from hex_sl.dialect.utils.placeholder import PlaceholderStyle
from . import SqlDriver

if TYPE_CHECKING:
    from hex_sl.project.dataset import Dataset


class ClickHouseDriver(SqlDriver):
    def __init__(self):
        import clickhouse_connect

        self.connection = clickhouse_connect.get_client(
            host="localhost", port=8123, username="default"
        )
        self.dialect = HexSLDialect.from_name("clickhouse")

    def evaluate_dataset(
        self, dataset: Dataset, parameters: dict[str, Any] = None, timezone: str = "UTC"
    ) -> pl.DataFrame:
        """
        Evaluate the given dataset's sql query using ClickHouse and return the results
        as a Polars DataFrame.

        Args:
            dataset (Dataset): The dataset to evaluate.
            parameters (dict[str, Any]): The parameters to use for the evaluation.
            timezone (str): The timezone to use for the evaluation.

        Returns:
            pl.DataFrame: The evaluation results as a Polars DataFrame.
        """
        sql, config = dataset.sql_placeholders(
            PlaceholderStyle.CLICKHOUSE, dialect=self.dialect
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

        pd_result = self.connection.query_df(
            sql,
            parameters=parameters,
            use_na_values=False,
            use_none=True,
            query_tz="UTC",
        )
        result = pl.from_pandas(pd_result)

        # The approach above converts clickhosue Dates to polars Datetimes
        # fix this here by looking at the true types from clickhouse
        if any(isinstance(dtype, pl.Datetime) for dtype in result.dtypes):
            clickhouse_dtypes = self.connection.query(sql).column_types
            for col, dtype in zip(result.columns, clickhouse_dtypes):
                if dtype.name == "Date" or dtype.name == "Nullable(Date)":
                    result = result.with_columns(pl.col(col).cast(pl.Date).alias(col))

        return self.convert_timezones(result, dataset.dimensions_list, timezone)

    def __del__(self):
        if hasattr(self, "connection"):
            self.connection.close()
