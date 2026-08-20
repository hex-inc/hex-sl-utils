"""In-process Spark SQL execution driver."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import polars as pl
from pyspark.sql import SparkSession  # type: ignore[reportMissingImports]

from database.driver.base import SqlDriver
from database.driver.query import RenderedQuery
from hex_sl_utils.placeholder import PlaceholderStyle


class SparkDriver(SqlDriver):
    dialect_name = "spark"
    placeholder_style = PlaceholderStyle.COLON_NAMED

    def __init__(self) -> None:
        self.temporary_directory = TemporaryDirectory(prefix="hex-sl-utils-spark-")
        setup_dir = Path(self.temporary_directory.name) / "spark_setup"
        store_dir = Path(self.temporary_directory.name) / "store"
        metastore_dir = store_dir / "metastore_db"
        warehouse_dir = store_dir / "warehouse"
        metastore_dir.mkdir(parents=True)
        warehouse_dir.mkdir(parents=True)
        setup_dir.mkdir()
        _write_hive_site(setup_dir, metastore_dir, warehouse_dir)

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
        self.spark.conf.set("spark.sql.ansi.enabled", "false")
        self.spark.conf.set("spark.sql.session.timeZone", "UTC")

    def execute_rendered(self, query: RenderedQuery) -> pl.DataFrame:
        """Execute one rendered Spark SQL query."""
        if not isinstance(query.parameters, dict):
            msg = "Spark requires named parameters"
            raise TypeError(msg)
        return pl.from_pandas(
            self.spark.sql(query.sql, args=query.parameters).toPandas()
        )

    def close(self) -> None:
        self.spark.stop()
        self.temporary_directory.cleanup()


def _write_hive_site(
    setup_directory: Path,
    metastore_directory: Path,
    warehouse_directory: Path,
) -> None:
    hive_site = f"""<configuration>
  <property>
    <name>javax.jdo.option.ConnectionURL</name>
    <value>jdbc:derby:;databaseName={metastore_directory};create=true</value>
  </property>
  <property>
    <name>spark.sql.warehouse.dir</name>
    <value>{warehouse_directory}</value>
  </property>
</configuration>
"""
    (setup_directory / "hive-site.xml").write_text(hive_site)
