from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import polars as pl
import polars.testing as pl_testing
import pytest
from inline_snapshot import snapshot

from hex_sl_utils.datatype import DataType
from hex_sl_utils.dialect import Dialect

from ..snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    columns = {
        "ts_tz": DataType.TIMESTAMPTZ,
    }
    timezone = "America/New_York"

    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            "year(ts_tz)",
            "quarter(ts_tz)",
            "month(ts_tz)",
            "day(ts_tz)",
            "dayofweek(ts_tz)",
            "hour(ts_tz)",
            "minute(ts_tz)",
            "second(ts_tz)",
            "millisecond(ts_tz)",
        ]

    @classmethod
    def get_expression_input_data(cls) -> pl.DataFrame:
        df = pl.DataFrame(
            {
                "ts_tz": [
                    datetime(2021, 1, 1, 0, 0, 0, 123000, tzinfo=ZoneInfo("UTC")),
                    datetime(2022, 5, 15, 14, 45, 30, 456000, tzinfo=ZoneInfo("UTC")),
                    datetime(2023, 12, 30, 18, 20, 15, 789000, tzinfo=ZoneInfo("UTC")),
                    datetime(2024, 9, 12, 23, 59, 59, 999000, tzinfo=ZoneInfo("UTC")),
                ]
            }
        )
        return df

    @classmethod
    def get_expected_df_from_input(
        cls, expression_input_data: pl.DataFrame, dialect: Dialect
    ) -> pl.DataFrame:
        """Get the expected results dataframe (computed in polars).

        Args:
            expression_input_data: The input data for the expressions
            dialect: The SQL dialect being tested

        Returns:
            pl.DataFrame: The expected results for validation
        """
        df = expression_input_data
        expected_df = pl.DataFrame(
            {
                "row": [0, 1, 2, 3],
                "col1": df.select(
                    pl.col("ts_tz").dt.convert_time_zone("America/New_York").dt.year()
                ),
                "col2": df.select(
                    pl.col("ts_tz")
                    .dt.convert_time_zone("America/New_York")
                    .dt.quarter()
                ),
                "col3": df.select(
                    pl.col("ts_tz").dt.convert_time_zone("America/New_York").dt.month()
                ),
                "col4": df.select(
                    pl.col("ts_tz").dt.convert_time_zone("America/New_York").dt.day()
                ),
                "col5": df.select(
                    pl.col("ts_tz")
                    .dt.convert_time_zone("America/New_York")
                    .dt.weekday()
                    % 7
                    + 1
                ),
                "col6": df.select(
                    pl.col("ts_tz").dt.convert_time_zone("America/New_York").dt.hour()
                ),
                "col7": df.select(
                    pl.col("ts_tz").dt.convert_time_zone("America/New_York").dt.minute()
                ),
                "col8": df.select(
                    pl.col("ts_tz").dt.convert_time_zone("America/New_York").dt.second()
                ),
                "col9": df.select(
                    pl.col("ts_tz")
                    .dt.convert_time_zone("America/New_York")
                    .dt.millisecond()
                ),
            }
        )
        return expected_df

    @classmethod
    def validate(
        cls, expected_df: pl.DataFrame, result_df: pl.DataFrame, dialect: Dialect
    ) -> None:
        """Validate the query results against expected values."""
        assert result_df.shape == (4, 10)
        pl_testing.assert_frame_equal(
            result_df, expected_df, check_dtypes=False, abs_tol=1e-6
        )


# Database result tests


def test_snapshot_datepart_ts_tz_validate(dialect_name):
    """Test datepart timestamp with timezone expressions for each dialect separately."""
    dialect = Dialect.from_name(dialect_name)
    result_df = SnapshotTest.get_result_df(dialect)
    expected_df = SnapshotTest.get_expected_df(dialect)
    SnapshotTest.validate(expected_df, result_df, dialect)


@pytest.mark.database
@pytest.mark.database_local
def test_snapshot_datepart_ts_tz_result():
    """Test datepart timestamp with timezone expressions for each dialect separately."""
    dialect_name = SnapshotTest.result_dialect
    dialect = Dialect.from_name(dialect_name)
    result_str = SnapshotTest.get_result_df_str(dialect)

    assert result_str == snapshot("""\
shape: (4, 10)
┌─────┬──────┬──────┬──────┬──────┬──────┬──────┬──────┬──────┬──────┐
│ row ┆ col1 ┆ col2 ┆ col3 ┆ col4 ┆ col5 ┆ col6 ┆ col7 ┆ col8 ┆ col9 │
│ --- ┆ ---  ┆ ---  ┆ ---  ┆ ---  ┆ ---  ┆ ---  ┆ ---  ┆ ---  ┆ ---  │
│ i32 ┆ i64  ┆ i64  ┆ i64  ┆ i64  ┆ i64  ┆ i64  ┆ i64  ┆ i64  ┆ i64  │
╞═════╪══════╪══════╪══════╪══════╪══════╪══════╪══════╪══════╪══════╡
│ 0   ┆ 2020 ┆ 4    ┆ 12   ┆ 31   ┆ 5    ┆ 19   ┆ 0    ┆ 0    ┆ 123  │
│ 1   ┆ 2022 ┆ 2    ┆ 5    ┆ 15   ┆ 1    ┆ 10   ┆ 45   ┆ 30   ┆ 456  │
│ 2   ┆ 2023 ┆ 4    ┆ 12   ┆ 30   ┆ 7    ┆ 13   ┆ 20   ┆ 15   ┆ 789  │
│ 3   ┆ 2024 ┆ 3    ┆ 9    ┆ 12   ┆ 5    ┆ 19   ┆ 59   ┆ 59   ┆ 999  │
└─────┴──────┴──────┴──────┴──────┴──────┴──────┴──────┴──────┴──────┘\
""")


# SQL expression snapshots


def test_snapshot_datepart_ts_tz_sql():
    """Snapshot directly compiled calc SQL for every supported dialect."""
    assert SnapshotTest.render_sql_snapshot() == snapshot("""\
-- === BIGQUERY ===
EXTRACT(YEAR FROM DATETIME(`ts_tz`, 'America/New_York'));
EXTRACT(QUARTER FROM DATETIME(`ts_tz`, 'America/New_York'));
EXTRACT(MONTH FROM DATETIME(`ts_tz`, 'America/New_York'));
EXTRACT(DAY FROM DATETIME(`ts_tz`, 'America/New_York'));
EXTRACT(DAYOFWEEK FROM DATETIME(`ts_tz`, 'America/New_York'));
EXTRACT(HOUR FROM DATETIME(`ts_tz`, 'America/New_York'));
EXTRACT(MINUTE FROM DATETIME(`ts_tz`, 'America/New_York'));
CAST(TRUNC(EXTRACT(SECOND FROM DATETIME(`ts_tz`, 'America/New_York'))) AS INT64);
MOD(EXTRACT(MILLISECOND FROM DATETIME(`ts_tz`, 'America/New_York')), 1000);

-- === CLICKHOUSE ===
EXTRACT(YEAR FROM toTimeZone("ts_tz", 'America/New_York'));
EXTRACT(QUARTER FROM toTimeZone("ts_tz", 'America/New_York'));
EXTRACT(MONTH FROM toTimeZone("ts_tz", 'America/New_York'));
EXTRACT(DAY FROM toTimeZone("ts_tz", 'America/New_York'));
toDayOfWeek(toTimeZone("ts_tz", 'America/New_York'), 3);
EXTRACT(HOUR FROM toTimeZone("ts_tz", 'America/New_York'));
EXTRACT(MINUTE FROM toTimeZone("ts_tz", 'America/New_York'));
CAST(EXTRACT(SECOND FROM toTimeZone("ts_tz", 'America/New_York')) AS Nullable(Int32));
EXTRACT(MILLISECOND FROM toTimeZone("ts_tz", 'America/New_York')) % 1000;

-- === DUCKDB ===
EXTRACT(YEAR FROM "ts_tz" AT TIME ZONE 'America/New_York');
EXTRACT(QUARTER FROM "ts_tz" AT TIME ZONE 'America/New_York');
EXTRACT(MONTH FROM "ts_tz" AT TIME ZONE 'America/New_York');
EXTRACT(DAY FROM "ts_tz" AT TIME ZONE 'America/New_York');
EXTRACT(DAYOFWEEK FROM "ts_tz" AT TIME ZONE 'America/New_York') + 1;
EXTRACT(HOUR FROM "ts_tz" AT TIME ZONE 'America/New_York');
EXTRACT(MINUTE FROM "ts_tz" AT TIME ZONE 'America/New_York');
CAST(EXTRACT(SECOND FROM "ts_tz" AT TIME ZONE 'America/New_York') AS BIGINT);
EXTRACT('MILLISECOND' FROM "ts_tz" AT TIME ZONE 'America/New_York') % 1000;

-- === MSSQL ===
DATEPART(YEAR, [ts_tz] AT TIME ZONE 'Eastern Standard Time');
DATEPART(QUARTER, [ts_tz] AT TIME ZONE 'Eastern Standard Time');
DATEPART(MONTH, [ts_tz] AT TIME ZONE 'Eastern Standard Time');
DATEPART(DAY, [ts_tz] AT TIME ZONE 'Eastern Standard Time');
DATEPART(DW, [ts_tz] AT TIME ZONE 'Eastern Standard Time');
DATEPART(HOUR, [ts_tz] AT TIME ZONE 'Eastern Standard Time');
DATEPART(MINUTE, [ts_tz] AT TIME ZONE 'Eastern Standard Time');
CAST(DATEPART(SECOND, [ts_tz] AT TIME ZONE 'Eastern Standard Time') AS INTEGER);
DATEPART(MILLISECOND, [ts_tz] AT TIME ZONE 'Eastern Standard Time') % 1000;

-- === MYSQL ===
EXTRACT(YEAR FROM CAST(CONVERT_TZ(`ts_tz`, 'UTC', 'America/New_York') AS DATETIME(3)));
EXTRACT(QUARTER FROM CAST(CONVERT_TZ(`ts_tz`, 'UTC', 'America/New_York') AS DATETIME(3)));
EXTRACT(MONTH FROM CAST(CONVERT_TZ(`ts_tz`, 'UTC', 'America/New_York') AS DATETIME(3)));
EXTRACT(DAY FROM CAST(CONVERT_TZ(`ts_tz`, 'UTC', 'America/New_York') AS DATETIME(3)));
DAYOFWEEK(CAST(CONVERT_TZ(`ts_tz`, 'UTC', 'America/New_York') AS DATETIME(3)));
EXTRACT(HOUR FROM CAST(CONVERT_TZ(`ts_tz`, 'UTC', 'America/New_York') AS DATETIME(3)));
EXTRACT(MINUTE FROM CAST(CONVERT_TZ(`ts_tz`, 'UTC', 'America/New_York') AS DATETIME(3)));
CAST(EXTRACT(SECOND FROM CAST(CONVERT_TZ(`ts_tz`, 'UTC', 'America/New_York') AS DATETIME(3))) AS SIGNED);
FLOOR(
  EXTRACT(microsecond FROM CAST(CONVERT_TZ(`ts_tz`, 'UTC', 'America/New_York') AS DATETIME(3))) / 1000
);

-- === POSTGRES ===
EXTRACT(YEAR FROM "ts_tz" AT TIME ZONE 'America/New_York');
EXTRACT(QUARTER FROM "ts_tz" AT TIME ZONE 'America/New_York');
EXTRACT(MONTH FROM "ts_tz" AT TIME ZONE 'America/New_York');
EXTRACT(DAY FROM "ts_tz" AT TIME ZONE 'America/New_York');
EXTRACT(dow FROM "ts_tz" AT TIME ZONE 'America/New_York') + 1;
EXTRACT(HOUR FROM "ts_tz" AT TIME ZONE 'America/New_York');
EXTRACT(MINUTE FROM "ts_tz" AT TIME ZONE 'America/New_York');
CAST(FLOOR(EXTRACT('second' FROM "ts_tz" AT TIME ZONE 'America/New_York')) AS INT);
CAST(FLOOR(EXTRACT('millisecond' FROM "ts_tz")) AS INT) % 1000;

-- === REDSHIFT ===
EXTRACT(YEAR FROM "ts_tz" AT TIME ZONE 'America/New_York');
EXTRACT(QUARTER FROM "ts_tz" AT TIME ZONE 'America/New_York');
EXTRACT(MONTH FROM "ts_tz" AT TIME ZONE 'America/New_York');
EXTRACT(DAY FROM "ts_tz" AT TIME ZONE 'America/New_York');
EXTRACT(dow FROM "ts_tz" AT TIME ZONE 'America/New_York') + 1;
EXTRACT(HOUR FROM "ts_tz" AT TIME ZONE 'America/New_York');
EXTRACT(MINUTE FROM "ts_tz" AT TIME ZONE 'America/New_York');
CAST(FLOOR(EXTRACT('second' FROM "ts_tz" AT TIME ZONE 'America/New_York')) AS INTEGER);
MOD(CAST(FLOOR(EXTRACT('millisecond' FROM "ts_tz")) AS INTEGER), 1000);

-- === SNOWFLAKE ===
DATE_PART(YEAR, CONVERT_TIMEZONE('America/New_York', "ts_tz"));
DATE_PART(QUARTER, CONVERT_TIMEZONE('America/New_York', "ts_tz"));
DATE_PART(MONTH, CONVERT_TIMEZONE('America/New_York', "ts_tz"));
DATE_PART(DAY, CONVERT_TIMEZONE('America/New_York', "ts_tz"));
DATE_PART(DAYOFWEEK, CONVERT_TIMEZONE('America/New_York', "ts_tz")) + 1;
DATE_PART('hour', CONVERT_TIMEZONE('America/New_York', "ts_tz"));
DATE_PART('minute', CONVERT_TIMEZONE('America/New_York', "ts_tz"));
CAST(DATE_PART('second', CONVERT_TIMEZONE('America/New_York', "ts_tz")) AS BIGINT);
DATE_PART('epoch_millisecond', CONVERT_TIMEZONE('America/New_York', "ts_tz")) % 1000;

-- === SPARK ===
EXTRACT(YEAR FROM CAST(CONVERT_TIMEZONE('UTC', 'America/New_York', `ts_tz`) AS TIMESTAMP));
EXTRACT(QUARTER FROM CAST(CONVERT_TIMEZONE('UTC', 'America/New_York', `ts_tz`) AS TIMESTAMP));
EXTRACT(MONTH FROM CAST(CONVERT_TIMEZONE('UTC', 'America/New_York', `ts_tz`) AS TIMESTAMP));
EXTRACT(DAY FROM CAST(CONVERT_TIMEZONE('UTC', 'America/New_York', `ts_tz`) AS TIMESTAMP));
DAYOFWEEK(TO_DATE(CAST(CONVERT_TIMEZONE('UTC', 'America/New_York', `ts_tz`) AS TIMESTAMP)));
EXTRACT(HOUR FROM CAST(CONVERT_TIMEZONE('UTC', 'America/New_York', `ts_tz`) AS TIMESTAMP));
EXTRACT(MINUTE FROM CAST(CONVERT_TIMEZONE('UTC', 'America/New_York', `ts_tz`) AS TIMESTAMP));
CAST(EXTRACT(SECOND FROM CAST(CONVERT_TIMEZONE('UTC', 'America/New_York', `ts_tz`) AS TIMESTAMP)) AS BIGINT);
CAST(DATE_FORMAT(CAST(CONVERT_TIMEZONE('UTC', 'America/New_York', `ts_tz`) AS TIMESTAMP), 'SSS') AS INT);

-- === TRINO ===
EXTRACT(YEAR FROM AT_TIMEZONE("ts_tz", 'America/New_York'));
EXTRACT(QUARTER FROM AT_TIMEZONE("ts_tz", 'America/New_York'));
EXTRACT(MONTH FROM AT_TIMEZONE("ts_tz", 'America/New_York'));
EXTRACT(DAY FROM AT_TIMEZONE("ts_tz", 'America/New_York'));
DAY_OF_WEEK(AT_TIMEZONE("ts_tz", 'America/New_York')) % 7 + 1;
EXTRACT(HOUR FROM AT_TIMEZONE("ts_tz", 'America/New_York'));
EXTRACT(MINUTE FROM AT_TIMEZONE("ts_tz", 'America/New_York'));
CAST(EXTRACT(SECOND FROM AT_TIMEZONE("ts_tz", 'America/New_York')) AS BIGINT);
MILLISECOND(AT_TIMEZONE("ts_tz", 'America/New_York'));
""")
