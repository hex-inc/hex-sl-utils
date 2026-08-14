from __future__ import annotations
import os
from pathlib import Path
import polars as pl
import sys
from typing import TYPE_CHECKING, Any, Optional
from pyspark.sql import SparkSession
from hex_sl.dialect.base import HexSLDialect
from hex_sl.dialect.utils.placeholder import PlaceholderStyle
from . import SqlDriver

# Add scripts directory to path to import get_main_dir
scripts_dir = Path(__file__).resolve().parent.parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))
from get_main_dir import get_main_dir  # noqa: E402

if TYPE_CHECKING:
    from hex_sl.project.dataset import Dataset


class SparkDriver(SqlDriver):
    def __init__(self) -> None:
        main_dir = Path(get_main_dir())
        # Get the path to the spark_setup directory
        setup_dir = main_dir / "scripts" / "spark_setup"
        store_dir = setup_dir / "store"
        metastore_dir = store_dir / "metastore_db"
        warehouse_dir = store_dir / "warehouse"

        # Ensure directories exist
        os.makedirs(metastore_dir, exist_ok=True)
        os.makedirs(warehouse_dir, exist_ok=True)

        self.spark: SparkSession = (
            SparkSession.builder.appName("HexSLSparkDriver")
            .config("spark.sql.warehouse.dir", str(warehouse_dir))
            .config("hive.metastore.warehouse.dir", str(warehouse_dir))
            .config(
                "javax.jdo.option.ConnectionURL",
                f"jdbc:derby:;databaseName={metastore_dir};create=true",
            )
            .config("spark.sql.hive.metastore.jars", "builtin")
            .config("spark.driver.extraClassPath", str(setup_dir))
            .config("hive.config.dir", str(setup_dir))
            .config("hive.metastore.uris", "")
            .config("spark.driver.bindAddress", "127.0.0.1")
            .config("spark.driver.host", "127.0.0.1")
            .enableHiveSupport()
            .master("local[*]")
            .getOrCreate()
        )
        # Set timezone to UTC
        self.spark.conf.set("spark.sql.session.timeZone", "UTC")
        self.dialect = HexSLDialect.from_name("spark")

    def evaluate_dataset(
        self,
        dataset: Dataset,
        parameters: Optional[dict[str, Any]] = None,
        timezone: str = "UTC",
    ) -> pl.DataFrame:
        """
        Evaluate the given dataset's sql query using Spark and return the results
        as a Polars DataFrame.

        Args:
            dataset (Dataset): The dataset to evaluate.
            parameters (dict[str, Any], optional): Parameters for the query.
            timezone (str): The timezone to use for the evaluation.

        Returns:
            pl.DataFrame: The evaluation results as a Polars DataFrame.
        """
        sql, config = dataset.sql_placeholders(
            PlaceholderStyle.COLON_NAMED, dialect=self.dialect
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

        # Execute the query
        spark_df = self.spark.sql(sql, args=parameters)

        # Convert Spark DataFrame to Polars DataFrame
        pdf = spark_df.toPandas()
        result = pl.from_pandas(pdf)

        return self.convert_timezones(result, dataset.dimensions_list, timezone)

    def __del__(self) -> None:
        if hasattr(self, "spark"):
            try:
                self.spark.stop()
            except Exception:  # noqa: BLE001
                pass
