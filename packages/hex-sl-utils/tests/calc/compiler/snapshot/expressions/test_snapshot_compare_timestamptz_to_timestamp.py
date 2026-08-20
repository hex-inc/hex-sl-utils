from __future__ import annotations

import zoneinfo
from datetime import datetime

import polars as pl
import pytest
from inline_snapshot import snapshot

from hex_sl_utils.datatype import DataType
from hex_sl_utils.dialect import Dialect

from ..snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    columns = {
        "tstz_col": DataType.TIMESTAMPTZ,
    }
    timezone = "America/New_York"

    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            # TimestampTz To Date
            "toNumber(tstz_col < ToDatetime('2021-01-02 10:00:00'))",
            "toNumber(tstz_col < ToDate('2021-01-02'))",
        ]

    @classmethod
    def get_expression_input_data(cls) -> pl.DataFrame:
        utc = zoneinfo.ZoneInfo("UTC")
        df = pl.DataFrame(
            {
                "tstz_col": [
                    datetime(2021, 1, 2, 12, 15, 30, tzinfo=utc),  # 12:15:30 UTC
                    datetime(2021, 1, 2, 14, 45, 45, tzinfo=utc),  # 14:45:45 UTC
                    datetime(2021, 1, 2, 17, 30, 10, tzinfo=utc),  # 17:30:10 UTC
                ],
            }
        )
        return df

    @classmethod
    def get_expected_df_from_input(
        cls, expression_input_data: pl.DataFrame, dialect: Dialect
    ) -> pl.DataFrame:
        df = expression_input_data
        tz = "America/New_York"
        expected_df = pl.DataFrame(
            {
                "row": [0, 1, 2],
                "col1": pl.select(
                    (
                        df["tstz_col"]
                        .dt.convert_time_zone(tz)
                        .dt.replace_time_zone(None)
                        < pl.datetime(2021, 1, 2, 10, 0, 0)
                    ).cast(pl.Int32),
                ),
                "col2": pl.select(
                    (
                        df["tstz_col"]
                        .dt.convert_time_zone(tz)
                        .dt.replace_time_zone(None)
                        < pl.datetime(2021, 1, 2, 0, 0, 0)
                    ).cast(pl.Int32),
                ),
            }
        )
        return expected_df


# Database result tests


def test_snapshot_compare_timestamptz_to_timestamp_validate(dialect_name):
    """Test compare timestamptz to timestamp expressions for each dialect separately."""
    dialect = Dialect.from_name(dialect_name)
    result_df = SnapshotTest.get_result_df(dialect, timezone="America/New_York")
    expected_df = SnapshotTest.get_expected_df(dialect)
    SnapshotTest.validate(expected_df, result_df, dialect)


@pytest.mark.database
@pytest.mark.database_local
def test_snapshot_compare_timestamptz_to_timestamp_result():
    """Test compare timestamptz to timestamp expressions for each dialect separately."""
    dialect_name = SnapshotTest.result_dialect
    dialect = Dialect.from_name(dialect_name)
    result_str = SnapshotTest.get_result_df_str(dialect, timezone="America/New_York")

    assert result_str == snapshot("""\
shape: (3, 3)
┌─────┬──────┬──────┐
│ row ┆ col1 ┆ col2 │
│ --- ┆ ---  ┆ ---  │
│ i32 ┆ i32  ┆ i32  │
╞═════╪══════╪══════╡
│ 0   ┆ 1    ┆ 0    │
│ 1   ┆ 1    ┆ 0    │
│ 2   ┆ 0    ┆ 0    │
└─────┴──────┴──────┘\
""")


# SQL expression snapshots


def test_snapshot_compare_timestamptz_to_timestamp_sql():
    """Snapshot directly compiled calc SQL for every supported dialect."""
    assert SnapshotTest.render_sql_snapshot() == snapshot("""\
-- === BIGQUERY ===
CASE
  WHEN `tstz_col` < TIMESTAMP(SAFE_CAST('2021-01-02 10:00:00' AS DATETIME), 'America/New_York')
  THEN 1
  ELSE 0
END;
CASE
  WHEN `tstz_col` < TIMESTAMP(CAST(SAFE_CAST('2021-01-02' AS DATE) AS DATETIME), 'America/New_York')
  THEN 1
  ELSE 0
END;

-- === CLICKHOUSE ===
CASE
  WHEN "tstz_col" < parseDateTime64BestEffortOrNull('2021-01-02 10:00:00', 3, 'America/New_York')
  THEN 1
  ELSE 0
END;
CASE
  WHEN "tstz_col" < toDateTime64(accurateCastOrNull('2021-01-02', 'Nullable(DATE)'), 3, 'America/New_York')
  THEN 1
  ELSE 0
END;

-- === DUCKDB ===
CASE
  WHEN "tstz_col" < TRY_CAST(TRY_STRPTIME(
    '2021-01-02 10:00:00',
    [
      '%Y-%m',
      '%Y-%m-%d',
      '%Y-%m-%dT%H:%M:%S',
      '%Y-%m-%dT%H:%M:%S.%g',
      '%Y-%m-%dT%H:%M:%S.%f',
      '%Y-%m-%dT%H:%M',
      '%Y-%m-%d %H:%M:%S',
      '%Y-%m-%d %H:%M:%S.%g',
      '%Y-%m-%d %H:%M:%S.%f',
      '%Y-%m-%d %H:%M',
      '%Y-%m-%dT%H:%M:%S%z',
      '%Y-%m-%dT%H:%M:%S.%g%z',
      '%Y-%m-%dT%H:%M:%S.%f%z',
      '%Y-%m-%dT%H:%M%z',
      '%Y-%m-%d %H:%M:%S%z',
      '%Y-%m-%d %H:%M:%S.%g%z',
      '%Y-%m-%d %H:%M:%S.%f%z',
      '%Y-%m-%d %H:%M%z',
      '%m/%d/%Y',
      '%m/%d/%Y %H:%M:%S',
      '%m/%d/%Y %H:%M:%S.%g',
      '%m/%d/%Y %H:%M:%S.%f',
      '%m/%d/%Y %H:%M',
      '%b %-d %Y',
      '%b %-d %Y %H:%M:%S',
      '%b %-d %Y %H:%M:%S.%g',
      '%b %-d %Y %H:%M:%S.%f',
      '%b %-d %Y %H:%M',
      '%a %b %-d %H:%M:%S %Y',
      '%a %b %-d %H:%M:%S.%g %Y',
      '%a %b %-d %H:%M:%S.%f %Y',
      '%a %b %-d %H:%M %Y',
      '%d %b %Y',
      '%d %b %Y %H:%M:%S',
      '%d %b %Y %H:%M:%S.%g',
      '%d %b %Y %H:%M:%S.%f',
      '%d %b %Y %H:%M',
      '%a, %d %b %Y',
      '%a, %d %b %Y %H:%M:%S',
      '%a, %d %b %Y %H:%M:%S.%g',
      '%a, %d %b %Y %H:%M:%S.%f',
      '%a, %d %b %Y %H:%M',
      '%B %d, %Y',
      '%B %d, %Y %H:%M:%S',
      '%B %d, %Y %H:%M:%S.%g',
      '%B %d, %Y %H:%M:%S.%f',
      '%B %d, %Y %H:%M',
      '%Y-%m-%dT%H:%M:%S%Z'
    ]
  ) AS TIMESTAMP) AT TIME ZONE 'America/New_York'
  THEN 1
  ELSE 0
END;
CASE
  WHEN "tstz_col" < CAST(TRY_CAST('2021-01-02' AS DATE) AS TIMESTAMP) AT TIME ZONE 'America/New_York'
  THEN 1
  ELSE 0
END;

-- === MSSQL ===
CASE
  WHEN [tstz_col] < TRY_CAST('2021-01-02 10:00:00' AS DATETIME2) AT TIME ZONE 'Eastern Standard Time'
  THEN 1
  ELSE 0
END;
CASE
  WHEN [tstz_col] < CAST(TRY_CAST('2021-01-02' AS DATE) AS DATETIME2) AT TIME ZONE 'Eastern Standard Time'
  THEN 1
  ELSE 0
END;

-- === MYSQL ===
CASE
  WHEN `tstz_col` < CAST(CONVERT_TZ(CAST('2021-01-02 10:00:00' AS DATETIME(3)), 'America/New_York', 'UTC') AS DATETIME)
  THEN 1
  ELSE 0
END;
CASE
  WHEN `tstz_col` < CAST(CONVERT_TZ(CAST(CAST('2021-01-02' AS DATE) AS DATETIME), 'America/New_York', 'UTC') AS DATETIME)
  THEN 1
  ELSE 0
END;

-- === POSTGRES ===
CASE
  WHEN "tstz_col" < CAST('2021-01-02 10:00:00' AS TIMESTAMP) AT TIME ZONE 'America/New_York'
  THEN 1
  ELSE 0
END;
CASE
  WHEN "tstz_col" < CAST(CASE
    WHEN '2021-01-02' ~ '^\\d{4}-\\d{2}-\\d{2}$'
    THEN CAST('2021-01-02' AS DATE)
    ELSE NULL
  END AS TIMESTAMP) AT TIME ZONE 'America/New_York'
  THEN 1
  ELSE 0
END;

-- === REDSHIFT ===
CASE
  WHEN "tstz_col" < CAST(CAST('2021-01-02 10:00:00' AS VARCHAR(MAX)) AS TIMESTAMP) AT TIME ZONE 'America/New_York'
  THEN 1
  ELSE 0
END;
CASE
  WHEN "tstz_col" < CAST(CASE
    WHEN CAST('2021-01-02' AS VARCHAR(MAX)) ~ '^\\\\d{4}-\\\\d{2}-\\\\d{2}$'
    THEN CAST(CAST('2021-01-02' AS VARCHAR(MAX)) AS DATE)
    ELSE NULL
  END AS TIMESTAMP) AT TIME ZONE 'America/New_York'
  THEN 1
  ELSE 0
END;

-- === SNOWFLAKE ===
CASE
  WHEN "tstz_col" < CONVERT_TIMEZONE(
    'America/New_York',
    TO_TIMESTAMP_TZ(
      CONCAT(
        TO_CHAR(
          CONVERT_TIMEZONE('America/New_York', 'UTC', CAST('2021-01-02 10:00:00.000000' AS TIMESTAMP)),
          'YYYY-MM-DD HH24:MI:SS.FF6'
        ),
        'Z'
      )
    )
  )
  THEN 1
  ELSE 0
END;
CASE
  WHEN "tstz_col" < CONVERT_TIMEZONE(
    'America/New_York',
    TO_TIMESTAMP_TZ(
      CONCAT(
        TO_CHAR(
          CONVERT_TIMEZONE('America/New_York', 'UTC', CAST(TRY_CAST('2021-01-02' AS DATE) AS TIMESTAMP)),
          'YYYY-MM-DD HH24:MI:SS.FF6'
        ),
        'Z'
      )
    )
  )
  THEN 1
  ELSE 0
END;

-- === SPARK ===
CASE
  WHEN `tstz_col` < CAST(CONVERT_TIMEZONE('America/New_York', 'UTC', CAST('2021-01-02 10:00:00' AS TIMESTAMP)) AS TIMESTAMP)
  THEN 1
  ELSE 0
END;
CASE
  WHEN `tstz_col` < CAST(CONVERT_TIMEZONE('America/New_York', 'UTC', CAST(CAST('2021-01-02' AS DATE) AS TIMESTAMP)) AS TIMESTAMP)
  THEN 1
  ELSE 0
END;

-- === TRINO ===
CASE
  WHEN "tstz_col" < WITH_TIMEZONE(TRY_CAST('2021-01-02 10:00:00' AS TIMESTAMP), 'America/New_York')
  THEN 1
  ELSE 0
END;
CASE
  WHEN "tstz_col" < WITH_TIMEZONE(CAST(TRY_CAST('2021-01-02' AS DATE) AS TIMESTAMP), 'America/New_York')
  THEN 1
  ELSE 0
END;
""")
