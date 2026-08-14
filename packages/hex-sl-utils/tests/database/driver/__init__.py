from __future__ import annotations
from abc import ABC, abstractmethod
import polars as pl
from typing import TYPE_CHECKING, Any, Optional
import os

from hex_sl.datatype import DataType
from hex_sl.dialect.bigquery import HexSLBigQuery
from hex_sl.dialect.redshift import HexSLRedshift
from hex_sl.dialect.snowflake import HexSLSnowflake
from hex_sl.dialect.trino import HexSLTrino
from hex_sl.dialect.clickhouse import HexSLClickHouse
from hex_sl.dialect.spark import HexSLSpark
from hex_sl.dialect.mssql import HexSLMSSQL
from hex_sl.dialect.mysql import HexSLMySQL
from hex_sl.dialect.postgres import HexSLPostgres
from hex_sl.semantic.dimension import Dimension


if TYPE_CHECKING:
    from hex_sl.dialect.base import HexSLDialect

    from hex_sl.project.dataset import Dataset


class SqlDriver(ABC):
    _driver_instances: dict[type[HexSLDialect], Optional[SqlDriver]] = {}

    @abstractmethod
    def evaluate_dataset(
        self, dataset: Dataset, parameters: dict[str, Any] = None, timezone: str = "UTC"
    ) -> pl.DataFrame:
        """
        Evaluate the given dataset and return the results as a Polars DataFrame.

        Args:
            dataset (Dataset): The dataset to evaluate.
            parameters (dict[str, Any]): Parameters to pass to the dataset.
            timezone (str): The timezone to use for the evaluation.
        Returns:
            pl.DataFrame: The evaluation results as a Polars DataFrame.
        """
        msg = f"SqlDriver/evaluate_dataset method for {self.__class__.__name__} is not implemented."
        raise NotImplementedError(msg)

    @classmethod
    def for_dialect(cls, dialect: HexSLDialect) -> Optional[SqlDriver]:
        """
        Return a SqlDriver instance for the given dialect, creating it if necessary.
        """
        from hex_sl.dialect.duckdb import HexSLDuckDB
        from tests.driver.duckdb import DuckDBDriver
        from tests.driver.clickhouse import ClickHouseDriver
        from tests.driver.postgres import PostgresDriver
        from tests.driver.mysql import MySqlDriver
        from tests.driver.spark import SparkDriver
        from tests.driver.mssql import MSSQLDriver
        from tests.driver.trino import TrinoDriver
        from tests.driver.snowflake import SnowflakeDriver
        from tests.driver.bigquery import BigQueryDriver
        from tests.driver.redshift import RedshiftDriver

        dialect_type = type(dialect)
        try:
            if dialect_type not in cls._driver_instances:
                if dialect_type == HexSLDuckDB:
                    cls._driver_instances[dialect_type] = DuckDBDriver()
                elif dialect_type == HexSLClickHouse:
                    cls._driver_instances[dialect_type] = ClickHouseDriver()
                elif dialect_type == HexSLPostgres:
                    cls._driver_instances[dialect_type] = PostgresDriver()
                elif dialect_type == HexSLMySQL:
                    cls._driver_instances[dialect_type] = MySqlDriver()
                elif dialect_type == HexSLSpark:
                    cls._driver_instances[dialect_type] = SparkDriver()
                elif dialect_type == HexSLMSSQL:
                    cls._driver_instances[dialect_type] = MSSQLDriver()
                elif dialect_type == HexSLTrino:
                    cls._driver_instances[dialect_type] = TrinoDriver()
                elif dialect_type == HexSLSnowflake:
                    cls._driver_instances[dialect_type] = SnowflakeDriver()
                elif dialect_type == HexSLBigQuery:
                    cls._driver_instances[dialect_type] = BigQueryDriver()
                elif dialect_type == HexSLRedshift:
                    cls._driver_instances[dialect_type] = RedshiftDriver()
                else:
                    cls._driver_instances[dialect_type] = None
        except ConnectionVarsNotSetError as e:
            if os.environ.get("HEX_SL_TEST_ALL_CONNECTIONS"):
                # If the HEX_SL_TEST_ALL_CONNECTIONS environment variable is set,
                # raise the error so the test will fail. We do this on CI to ensure
                # that connections aren't skipped due to missing environment variables.
                raise e
            else:
                cls._driver_instances[dialect_type] = None

        return cls._driver_instances[dialect_type]

    def convert_timezones(
        self,
        df: pl.DataFrame,
        dimensions: list[Dimension],
        timezone: str,
    ) -> pl.DataFrame:
        """
        Convert timezone-aware timestamp columns to the input timezone.
        """
        new_cols = {}
        dim_types = {dim.name: dim.type for dim in dimensions}
        for col in df.columns:
            if col not in dim_types:
                new_cols[col] = df[col]
                continue

            expected_dtype = dim_types[col]
            dtype = df[col].dtype

            if (
                isinstance(dtype, pl.Datetime)
                and expected_dtype == DataType.TIMESTAMPTZ
            ):
                if dtype.time_zone is None:
                    # If we expect a timestamptz but the column is not timezone-aware, treat as UTC
                    new_cols[col] = df.select(
                        df[col]
                        .dt.replace_time_zone("UTC")
                        .dt.convert_time_zone(timezone)
                    )
                else:
                    # If column is timezone-aware, convert to the input timezone
                    new_cols[col] = df.select(df[col].dt.convert_time_zone(timezone))
            else:
                new_cols[col] = df[col]

        return pl.DataFrame(new_cols)


class ConnectionVarsNotSetError(Exception):
    """
    An error that is raised when the connection environment variables for a driver are not set.
    """

    def __init__(self, var_name: str, driver_name: str):
        super().__init__(
            f"Connection environment variable {var_name} not set for "
            f"{driver_name} driver."
        )


def get_env_var(name: str, driver_name: str) -> str:
    """
    Get the environment variable for the given name.
    """
    value = os.environ.get(name)
    if value is None:
        raise ConnectionVarsNotSetError(name, driver_name)
    return value
