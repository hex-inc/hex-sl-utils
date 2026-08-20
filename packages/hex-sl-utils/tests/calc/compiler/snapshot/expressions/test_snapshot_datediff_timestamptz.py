from __future__ import annotations

from datetime import datetime

import polars as pl
import polars.testing as pl_testing
import pytest
import pytz
from inline_snapshot import snapshot

from hex_sl_utils.datatype import DataType
from hex_sl_utils.dialect import Dialect

from ..snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    columns = {
        "d1": DataType.TIMESTAMPTZ,
        "d2": DataType.TIMESTAMPTZ,
    }
    timezone = "America/New_York"

    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            "diffweeks(d1, d2)",
            "diffdays(d1, d2)",
            "diffhours(d1, d2)",
            "diffminutes(d1, d2)",
            "diffseconds(d1, d2)",
            "diffmilliseconds(d1, d2)",
        ]

    @classmethod
    def get_expression_input_data(cls) -> pl.DataFrame:
        tzinfo = pytz.timezone("America/New_York")
        df = pl.DataFrame(
            {
                "d1": [
                    datetime(2021, 1, 1, 1, 2, 23, 123000, tzinfo=tzinfo),
                    datetime(2022, 5, 15, 1, 2, 3, 456000, tzinfo=tzinfo),
                    datetime(2023, 12, 30, 1, 2, 3, 432000, tzinfo=tzinfo),
                    datetime(2024, 9, 12, 1, 2, 43, 321000, tzinfo=tzinfo),
                ],
                "d2": [
                    datetime(2021, 1, 2, 7, 3, 4, 987000, tzinfo=tzinfo),
                    datetime(2022, 2, 3, 0, 3, 1, 123000, tzinfo=tzinfo),
                    datetime(2023, 12, 31, 1, 2, 3, 456000, tzinfo=tzinfo),
                    datetime(2024, 10, 13, 1, 2, 3, 789000, tzinfo=tzinfo),
                ],
            }
        )
        return df

    @classmethod
    def get_expected_df_from_input(
        cls, expression_input_data: pl.DataFrame, dialect: Dialect
    ) -> pl.DataFrame:
        df = expression_input_data
        diff_ms = df.select(
            pl.col("d2").dt.timestamp("ms") - pl.col("d1").dt.timestamp("ms")
        )

        expected_df = pl.DataFrame(
            {
                "row": [0, 1, 2, 3],
                "col1": df.select(diff_ms / (1000 * 60 * 60 * 24 * 7)),
                "col2": df.select(diff_ms / (1000 * 60 * 60 * 24)),
                "col3": df.select(diff_ms / (1000 * 60 * 60)),
                "col4": df.select(diff_ms / (1000 * 60)),
                "col5": df.select(diff_ms / 1000),
                "col6": df.select(diff_ms),
            }
        )
        return expected_df

    @classmethod
    def validate(
        cls, expected_df: pl.DataFrame, result_df: pl.DataFrame, dialect: Dialect
    ) -> None:
        # Convert the result to the expected schema, to handle Decimals
        result_df = result_df.cast(expected_df.schema)

        pl_testing.assert_frame_equal(
            result_df, expected_df, check_dtypes=False, abs_tol=1e-2
        )


# Database result tests


def test_snapshot_datediff_timestamptz_validate(dialect_name):
    """Test datediff timestamptz expressions for each dialect separately."""
    dialect = Dialect.from_name(dialect_name)
    result_df = SnapshotTest.get_result_df(dialect, timezone="America/New_York")
    expected_df = SnapshotTest.get_expected_df(dialect)
    SnapshotTest.validate(expected_df, result_df, dialect)


@pytest.mark.database
@pytest.mark.database_local
def test_snapshot_datediff_timestamptz_result():
    """Test datediff timestamptz expressions for each dialect separately."""
    dialect_name = SnapshotTest.result_dialect
    dialect = Dialect.from_name(dialect_name)
    result_str = SnapshotTest.get_result_df_str(dialect, timezone="America/New_York")

    assert result_str == snapshot("""\
shape: (4, 7)
┌─────┬────────────┬─────────────┬──────────────┬────────────────┬────────────┬──────────────┐
│ row ┆ col1       ┆ col2        ┆ col3         ┆ col4           ┆ col5       ┆ col6         │
│ --- ┆ ---        ┆ ---         ┆ ---          ┆ ---            ┆ ---        ┆ ---          │
│ i32 ┆ f64        ┆ f64         ┆ f64          ┆ f64            ┆ f64        ┆ f64          │
╞═════╪════════════╪═════════════╪══════════════╪════════════════╪════════════╪══════════════╡
│ 0   ┆ 0.178641   ┆ 1.250485    ┆ 30.011629    ┆ 1800.697733    ┆ 108041.864 ┆ 1.08041864e8 │
│ 1   ┆ -14.434428 ┆ -101.040999 ┆ -2424.983981 ┆ -145499.038883 ┆ -8.7299e6  ┆ -8.7299e9    │
│ 2   ┆ 0.142857   ┆ 1.0         ┆ 24.000007    ┆ 1440.0004      ┆ 86400.024  ┆ 8.6400024e7  │
│ 3   ┆ 4.428506   ┆ 30.999542   ┆ 743.989019   ┆ 44639.341133   ┆ 2.6784e6   ┆ 2.6784e9     │
└─────┴────────────┴─────────────┴──────────────┴────────────────┴────────────┴──────────────┘\
""")


# SQL expression snapshots


def test_snapshot_datediff_timestamptz_sql():
    """Snapshot directly compiled calc SQL for every supported dialect."""
    assert SnapshotTest.render_sql_snapshot() == snapshot("""\
-- === BIGQUERY ===
(
  IF(NOT `d2` IS NULL, UNIX_MILLIS(TIMESTAMP(DATETIME(`d2`, 'UTC'))), NULL) - IF(NOT `d1` IS NULL, UNIX_MILLIS(TIMESTAMP(DATETIME(`d1`, 'UTC'))), NULL)
) / 604800000.0;
(
  IF(NOT `d2` IS NULL, UNIX_MILLIS(TIMESTAMP(DATETIME(`d2`, 'UTC'))), NULL) - IF(NOT `d1` IS NULL, UNIX_MILLIS(TIMESTAMP(DATETIME(`d1`, 'UTC'))), NULL)
) / 86400000.0;
(
  IF(NOT `d2` IS NULL, UNIX_MILLIS(TIMESTAMP(DATETIME(`d2`, 'UTC'))), NULL) - IF(NOT `d1` IS NULL, UNIX_MILLIS(TIMESTAMP(DATETIME(`d1`, 'UTC'))), NULL)
) / 3600000.0;
(
  IF(NOT `d2` IS NULL, UNIX_MILLIS(TIMESTAMP(DATETIME(`d2`, 'UTC'))), NULL) - IF(NOT `d1` IS NULL, UNIX_MILLIS(TIMESTAMP(DATETIME(`d1`, 'UTC'))), NULL)
) / 60000.0;
(
  IF(NOT `d2` IS NULL, UNIX_MILLIS(TIMESTAMP(DATETIME(`d2`, 'UTC'))), NULL) - IF(NOT `d1` IS NULL, UNIX_MILLIS(TIMESTAMP(DATETIME(`d1`, 'UTC'))), NULL)
) / 1000.0;
(
  IF(NOT `d2` IS NULL, UNIX_MILLIS(TIMESTAMP(DATETIME(`d2`, 'UTC'))), NULL) - IF(NOT `d1` IS NULL, UNIX_MILLIS(TIMESTAMP(DATETIME(`d1`, 'UTC'))), NULL)
) / 1.0;

-- === CLICKHOUSE ===
(
  (
    toUnixTimestamp64Milli("d2")
  ) - (
    toUnixTimestamp64Milli("d1")
  )
) / 604800000.0;
(
  (
    toUnixTimestamp64Milli("d2")
  ) - (
    toUnixTimestamp64Milli("d1")
  )
) / 86400000.0;
(
  (
    toUnixTimestamp64Milli("d2")
  ) - (
    toUnixTimestamp64Milli("d1")
  )
) / 3600000.0;
(
  (
    toUnixTimestamp64Milli("d2")
  ) - (
    toUnixTimestamp64Milli("d1")
  )
) / 60000.0;
(
  (
    toUnixTimestamp64Milli("d2")
  ) - (
    toUnixTimestamp64Milli("d1")
  )
) / 1000.0;
(
  (
    toUnixTimestamp64Milli("d2")
  ) - (
    toUnixTimestamp64Milli("d1")
  )
) / 1.0;

-- === DUCKDB ===
(
  CAST(EPOCH_MS("d2" AT TIME ZONE 'UTC') AS BIGINT) - CAST(EPOCH_MS("d1" AT TIME ZONE 'UTC') AS BIGINT)
) / 604800000.0;
(
  CAST(EPOCH_MS("d2" AT TIME ZONE 'UTC') AS BIGINT) - CAST(EPOCH_MS("d1" AT TIME ZONE 'UTC') AS BIGINT)
) / 86400000.0;
(
  CAST(EPOCH_MS("d2" AT TIME ZONE 'UTC') AS BIGINT) - CAST(EPOCH_MS("d1" AT TIME ZONE 'UTC') AS BIGINT)
) / 3600000.0;
(
  CAST(EPOCH_MS("d2" AT TIME ZONE 'UTC') AS BIGINT) - CAST(EPOCH_MS("d1" AT TIME ZONE 'UTC') AS BIGINT)
) / 60000.0;
(
  CAST(EPOCH_MS("d2" AT TIME ZONE 'UTC') AS BIGINT) - CAST(EPOCH_MS("d1" AT TIME ZONE 'UTC') AS BIGINT)
) / 1000.0;
(
  CAST(EPOCH_MS("d2" AT TIME ZONE 'UTC') AS BIGINT) - CAST(EPOCH_MS("d1" AT TIME ZONE 'UTC') AS BIGINT)
) / 1.0;

-- === MSSQL ===
CAST((
  (
    (
      CAST(DATEDIFF(
        SECOND,
        CAST('1970-01-01 00:00:00' AS DATETIME2),
        CAST([d2] AT TIME ZONE 'UTC' AS DATETIME2)
      ) AS BIGINT) * 1000
    ) + DATEPART(millisecond, [d2] AT TIME ZONE 'UTC')
  ) - (
    (
      CAST(DATEDIFF(
        SECOND,
        CAST('1970-01-01 00:00:00' AS DATETIME2),
        CAST([d1] AT TIME ZONE 'UTC' AS DATETIME2)
      ) AS BIGINT) * 1000
    ) + DATEPART(millisecond, [d1] AT TIME ZONE 'UTC')
  )
) AS FLOAT) / 604800000.0;
CAST((
  (
    (
      CAST(DATEDIFF(
        SECOND,
        CAST('1970-01-01 00:00:00' AS DATETIME2),
        CAST([d2] AT TIME ZONE 'UTC' AS DATETIME2)
      ) AS BIGINT) * 1000
    ) + DATEPART(millisecond, [d2] AT TIME ZONE 'UTC')
  ) - (
    (
      CAST(DATEDIFF(
        SECOND,
        CAST('1970-01-01 00:00:00' AS DATETIME2),
        CAST([d1] AT TIME ZONE 'UTC' AS DATETIME2)
      ) AS BIGINT) * 1000
    ) + DATEPART(millisecond, [d1] AT TIME ZONE 'UTC')
  )
) AS FLOAT) / 86400000.0;
CAST((
  (
    (
      CAST(DATEDIFF(
        SECOND,
        CAST('1970-01-01 00:00:00' AS DATETIME2),
        CAST([d2] AT TIME ZONE 'UTC' AS DATETIME2)
      ) AS BIGINT) * 1000
    ) + DATEPART(millisecond, [d2] AT TIME ZONE 'UTC')
  ) - (
    (
      CAST(DATEDIFF(
        SECOND,
        CAST('1970-01-01 00:00:00' AS DATETIME2),
        CAST([d1] AT TIME ZONE 'UTC' AS DATETIME2)
      ) AS BIGINT) * 1000
    ) + DATEPART(millisecond, [d1] AT TIME ZONE 'UTC')
  )
) AS FLOAT) / 3600000.0;
CAST((
  (
    (
      CAST(DATEDIFF(
        SECOND,
        CAST('1970-01-01 00:00:00' AS DATETIME2),
        CAST([d2] AT TIME ZONE 'UTC' AS DATETIME2)
      ) AS BIGINT) * 1000
    ) + DATEPART(millisecond, [d2] AT TIME ZONE 'UTC')
  ) - (
    (
      CAST(DATEDIFF(
        SECOND,
        CAST('1970-01-01 00:00:00' AS DATETIME2),
        CAST([d1] AT TIME ZONE 'UTC' AS DATETIME2)
      ) AS BIGINT) * 1000
    ) + DATEPART(millisecond, [d1] AT TIME ZONE 'UTC')
  )
) AS FLOAT) / 60000.0;
CAST((
  (
    (
      CAST(DATEDIFF(
        SECOND,
        CAST('1970-01-01 00:00:00' AS DATETIME2),
        CAST([d2] AT TIME ZONE 'UTC' AS DATETIME2)
      ) AS BIGINT) * 1000
    ) + DATEPART(millisecond, [d2] AT TIME ZONE 'UTC')
  ) - (
    (
      CAST(DATEDIFF(
        SECOND,
        CAST('1970-01-01 00:00:00' AS DATETIME2),
        CAST([d1] AT TIME ZONE 'UTC' AS DATETIME2)
      ) AS BIGINT) * 1000
    ) + DATEPART(millisecond, [d1] AT TIME ZONE 'UTC')
  )
) AS FLOAT) / 1000.0;
CAST((
  (
    (
      CAST(DATEDIFF(
        SECOND,
        CAST('1970-01-01 00:00:00' AS DATETIME2),
        CAST([d2] AT TIME ZONE 'UTC' AS DATETIME2)
      ) AS BIGINT) * 1000
    ) + DATEPART(millisecond, [d2] AT TIME ZONE 'UTC')
  ) - (
    (
      CAST(DATEDIFF(
        SECOND,
        CAST('1970-01-01 00:00:00' AS DATETIME2),
        CAST([d1] AT TIME ZONE 'UTC' AS DATETIME2)
      ) AS BIGINT) * 1000
    ) + DATEPART(millisecond, [d1] AT TIME ZONE 'UTC')
  )
) AS FLOAT) / 1.0;

-- === MYSQL ===
(
  FLOOR(UNIX_TIMESTAMP(CAST(CONVERT_TZ(`d2`, 'UTC', 'UTC') AS DATETIME(3))) * 1000) - FLOOR(UNIX_TIMESTAMP(CAST(CONVERT_TZ(`d1`, 'UTC', 'UTC') AS DATETIME(3))) * 1000)
) / 604800000.0;
(
  FLOOR(UNIX_TIMESTAMP(CAST(CONVERT_TZ(`d2`, 'UTC', 'UTC') AS DATETIME(3))) * 1000) - FLOOR(UNIX_TIMESTAMP(CAST(CONVERT_TZ(`d1`, 'UTC', 'UTC') AS DATETIME(3))) * 1000)
) / 86400000.0;
(
  FLOOR(UNIX_TIMESTAMP(CAST(CONVERT_TZ(`d2`, 'UTC', 'UTC') AS DATETIME(3))) * 1000) - FLOOR(UNIX_TIMESTAMP(CAST(CONVERT_TZ(`d1`, 'UTC', 'UTC') AS DATETIME(3))) * 1000)
) / 3600000.0;
(
  FLOOR(UNIX_TIMESTAMP(CAST(CONVERT_TZ(`d2`, 'UTC', 'UTC') AS DATETIME(3))) * 1000) - FLOOR(UNIX_TIMESTAMP(CAST(CONVERT_TZ(`d1`, 'UTC', 'UTC') AS DATETIME(3))) * 1000)
) / 60000.0;
(
  FLOOR(UNIX_TIMESTAMP(CAST(CONVERT_TZ(`d2`, 'UTC', 'UTC') AS DATETIME(3))) * 1000) - FLOOR(UNIX_TIMESTAMP(CAST(CONVERT_TZ(`d1`, 'UTC', 'UTC') AS DATETIME(3))) * 1000)
) / 1000.0;
(
  FLOOR(UNIX_TIMESTAMP(CAST(CONVERT_TZ(`d2`, 'UTC', 'UTC') AS DATETIME(3))) * 1000) - FLOOR(UNIX_TIMESTAMP(CAST(CONVERT_TZ(`d1`, 'UTC', 'UTC') AS DATETIME(3))) * 1000)
) / 1.0;

-- === POSTGRES ===
CAST((
  CAST(FLOOR(EXTRACT('epoch' FROM "d2" AT TIME ZONE 'UTC') * 1000) AS BIGINT) - CAST(FLOOR(EXTRACT('epoch' FROM "d1" AT TIME ZONE 'UTC') * 1000) AS BIGINT)
) AS DOUBLE PRECISION) / 604800000.0;
CAST((
  CAST(FLOOR(EXTRACT('epoch' FROM "d2" AT TIME ZONE 'UTC') * 1000) AS BIGINT) - CAST(FLOOR(EXTRACT('epoch' FROM "d1" AT TIME ZONE 'UTC') * 1000) AS BIGINT)
) AS DOUBLE PRECISION) / 86400000.0;
CAST((
  CAST(FLOOR(EXTRACT('epoch' FROM "d2" AT TIME ZONE 'UTC') * 1000) AS BIGINT) - CAST(FLOOR(EXTRACT('epoch' FROM "d1" AT TIME ZONE 'UTC') * 1000) AS BIGINT)
) AS DOUBLE PRECISION) / 3600000.0;
CAST((
  CAST(FLOOR(EXTRACT('epoch' FROM "d2" AT TIME ZONE 'UTC') * 1000) AS BIGINT) - CAST(FLOOR(EXTRACT('epoch' FROM "d1" AT TIME ZONE 'UTC') * 1000) AS BIGINT)
) AS DOUBLE PRECISION) / 60000.0;
CAST((
  CAST(FLOOR(EXTRACT('epoch' FROM "d2" AT TIME ZONE 'UTC') * 1000) AS BIGINT) - CAST(FLOOR(EXTRACT('epoch' FROM "d1" AT TIME ZONE 'UTC') * 1000) AS BIGINT)
) AS DOUBLE PRECISION) / 1000.0;
CAST((
  CAST(FLOOR(EXTRACT('epoch' FROM "d2" AT TIME ZONE 'UTC') * 1000) AS BIGINT) - CAST(FLOOR(EXTRACT('epoch' FROM "d1" AT TIME ZONE 'UTC') * 1000) AS BIGINT)
) AS DOUBLE PRECISION) / 1.0;

-- === REDSHIFT ===
CAST((
  (
    (
      CAST(EXTRACT('millisecond' FROM "d2" AT TIME ZONE 'UTC') AS BIGINT)
    ) + (
      CAST(EXTRACT('epoch' FROM "d2" AT TIME ZONE 'UTC') AS BIGINT) * 1000
    )
  ) - (
    (
      CAST(EXTRACT('millisecond' FROM "d1" AT TIME ZONE 'UTC') AS BIGINT)
    ) + (
      CAST(EXTRACT('epoch' FROM "d1" AT TIME ZONE 'UTC') AS BIGINT) * 1000
    )
  )
) AS DOUBLE PRECISION) / 604800000.0;
CAST((
  (
    (
      CAST(EXTRACT('millisecond' FROM "d2" AT TIME ZONE 'UTC') AS BIGINT)
    ) + (
      CAST(EXTRACT('epoch' FROM "d2" AT TIME ZONE 'UTC') AS BIGINT) * 1000
    )
  ) - (
    (
      CAST(EXTRACT('millisecond' FROM "d1" AT TIME ZONE 'UTC') AS BIGINT)
    ) + (
      CAST(EXTRACT('epoch' FROM "d1" AT TIME ZONE 'UTC') AS BIGINT) * 1000
    )
  )
) AS DOUBLE PRECISION) / 86400000.0;
CAST((
  (
    (
      CAST(EXTRACT('millisecond' FROM "d2" AT TIME ZONE 'UTC') AS BIGINT)
    ) + (
      CAST(EXTRACT('epoch' FROM "d2" AT TIME ZONE 'UTC') AS BIGINT) * 1000
    )
  ) - (
    (
      CAST(EXTRACT('millisecond' FROM "d1" AT TIME ZONE 'UTC') AS BIGINT)
    ) + (
      CAST(EXTRACT('epoch' FROM "d1" AT TIME ZONE 'UTC') AS BIGINT) * 1000
    )
  )
) AS DOUBLE PRECISION) / 3600000.0;
CAST((
  (
    (
      CAST(EXTRACT('millisecond' FROM "d2" AT TIME ZONE 'UTC') AS BIGINT)
    ) + (
      CAST(EXTRACT('epoch' FROM "d2" AT TIME ZONE 'UTC') AS BIGINT) * 1000
    )
  ) - (
    (
      CAST(EXTRACT('millisecond' FROM "d1" AT TIME ZONE 'UTC') AS BIGINT)
    ) + (
      CAST(EXTRACT('epoch' FROM "d1" AT TIME ZONE 'UTC') AS BIGINT) * 1000
    )
  )
) AS DOUBLE PRECISION) / 60000.0;
CAST((
  (
    (
      CAST(EXTRACT('millisecond' FROM "d2" AT TIME ZONE 'UTC') AS BIGINT)
    ) + (
      CAST(EXTRACT('epoch' FROM "d2" AT TIME ZONE 'UTC') AS BIGINT) * 1000
    )
  ) - (
    (
      CAST(EXTRACT('millisecond' FROM "d1" AT TIME ZONE 'UTC') AS BIGINT)
    ) + (
      CAST(EXTRACT('epoch' FROM "d1" AT TIME ZONE 'UTC') AS BIGINT) * 1000
    )
  )
) AS DOUBLE PRECISION) / 1000.0;
CAST((
  (
    (
      CAST(EXTRACT('millisecond' FROM "d2" AT TIME ZONE 'UTC') AS BIGINT)
    ) + (
      CAST(EXTRACT('epoch' FROM "d2" AT TIME ZONE 'UTC') AS BIGINT) * 1000
    )
  ) - (
    (
      CAST(EXTRACT('millisecond' FROM "d1" AT TIME ZONE 'UTC') AS BIGINT)
    ) + (
      CAST(EXTRACT('epoch' FROM "d1" AT TIME ZONE 'UTC') AS BIGINT) * 1000
    )
  )
) AS DOUBLE PRECISION) / 1.0;

-- === SNOWFLAKE ===
(
  DATE_PART('epoch_millisecond', CONVERT_TIMEZONE('UTC', "d2")) - DATE_PART('epoch_millisecond', CONVERT_TIMEZONE('UTC', "d1"))
) / 604800000.0;
(
  DATE_PART('epoch_millisecond', CONVERT_TIMEZONE('UTC', "d2")) - DATE_PART('epoch_millisecond', CONVERT_TIMEZONE('UTC', "d1"))
) / 86400000.0;
(
  DATE_PART('epoch_millisecond', CONVERT_TIMEZONE('UTC', "d2")) - DATE_PART('epoch_millisecond', CONVERT_TIMEZONE('UTC', "d1"))
) / 3600000.0;
(
  DATE_PART('epoch_millisecond', CONVERT_TIMEZONE('UTC', "d2")) - DATE_PART('epoch_millisecond', CONVERT_TIMEZONE('UTC', "d1"))
) / 60000.0;
(
  DATE_PART('epoch_millisecond', CONVERT_TIMEZONE('UTC', "d2")) - DATE_PART('epoch_millisecond', CONVERT_TIMEZONE('UTC', "d1"))
) / 1000.0;
(
  DATE_PART('epoch_millisecond', CONVERT_TIMEZONE('UTC', "d2")) - DATE_PART('epoch_millisecond', CONVERT_TIMEZONE('UTC', "d1"))
) / 1.0;

-- === SPARK ===
(
  (
    UNIX_TIMESTAMP(`d2`) * 1000 + CAST(EXTRACT(seconds FROM `d2`) % 1 * 1000 AS BIGINT)
  ) - (
    UNIX_TIMESTAMP(`d1`) * 1000 + CAST(EXTRACT(seconds FROM `d1`) % 1 * 1000 AS BIGINT)
  )
) / 604800000.0;
(
  (
    UNIX_TIMESTAMP(`d2`) * 1000 + CAST(EXTRACT(seconds FROM `d2`) % 1 * 1000 AS BIGINT)
  ) - (
    UNIX_TIMESTAMP(`d1`) * 1000 + CAST(EXTRACT(seconds FROM `d1`) % 1 * 1000 AS BIGINT)
  )
) / 86400000.0;
(
  (
    UNIX_TIMESTAMP(`d2`) * 1000 + CAST(EXTRACT(seconds FROM `d2`) % 1 * 1000 AS BIGINT)
  ) - (
    UNIX_TIMESTAMP(`d1`) * 1000 + CAST(EXTRACT(seconds FROM `d1`) % 1 * 1000 AS BIGINT)
  )
) / 3600000.0;
(
  (
    UNIX_TIMESTAMP(`d2`) * 1000 + CAST(EXTRACT(seconds FROM `d2`) % 1 * 1000 AS BIGINT)
  ) - (
    UNIX_TIMESTAMP(`d1`) * 1000 + CAST(EXTRACT(seconds FROM `d1`) % 1 * 1000 AS BIGINT)
  )
) / 60000.0;
(
  (
    UNIX_TIMESTAMP(`d2`) * 1000 + CAST(EXTRACT(seconds FROM `d2`) % 1 * 1000 AS BIGINT)
  ) - (
    UNIX_TIMESTAMP(`d1`) * 1000 + CAST(EXTRACT(seconds FROM `d1`) % 1 * 1000 AS BIGINT)
  )
) / 1000.0;
(
  (
    UNIX_TIMESTAMP(`d2`) * 1000 + CAST(EXTRACT(seconds FROM `d2`) % 1 * 1000 AS BIGINT)
  ) - (
    UNIX_TIMESTAMP(`d1`) * 1000 + CAST(EXTRACT(seconds FROM `d1`) % 1 * 1000 AS BIGINT)
  )
) / 1.0;

-- === TRINO ===
CAST((
  CAST(FLOOR(TO_UNIXTIME(AT_TIMEZONE("d2", 'UTC')) * 1000) AS BIGINT) - CAST(FLOOR(TO_UNIXTIME(AT_TIMEZONE("d1", 'UTC')) * 1000) AS BIGINT)
) AS DOUBLE) / 604800000.0;
CAST((
  CAST(FLOOR(TO_UNIXTIME(AT_TIMEZONE("d2", 'UTC')) * 1000) AS BIGINT) - CAST(FLOOR(TO_UNIXTIME(AT_TIMEZONE("d1", 'UTC')) * 1000) AS BIGINT)
) AS DOUBLE) / 86400000.0;
CAST((
  CAST(FLOOR(TO_UNIXTIME(AT_TIMEZONE("d2", 'UTC')) * 1000) AS BIGINT) - CAST(FLOOR(TO_UNIXTIME(AT_TIMEZONE("d1", 'UTC')) * 1000) AS BIGINT)
) AS DOUBLE) / 3600000.0;
CAST((
  CAST(FLOOR(TO_UNIXTIME(AT_TIMEZONE("d2", 'UTC')) * 1000) AS BIGINT) - CAST(FLOOR(TO_UNIXTIME(AT_TIMEZONE("d1", 'UTC')) * 1000) AS BIGINT)
) AS DOUBLE) / 60000.0;
CAST((
  CAST(FLOOR(TO_UNIXTIME(AT_TIMEZONE("d2", 'UTC')) * 1000) AS BIGINT) - CAST(FLOOR(TO_UNIXTIME(AT_TIMEZONE("d1", 'UTC')) * 1000) AS BIGINT)
) AS DOUBLE) / 1000.0;
CAST((
  CAST(FLOOR(TO_UNIXTIME(AT_TIMEZONE("d2", 'UTC')) * 1000) AS BIGINT) - CAST(FLOOR(TO_UNIXTIME(AT_TIMEZONE("d1", 'UTC')) * 1000) AS BIGINT)
) AS DOUBLE) / 1.0;
""")
