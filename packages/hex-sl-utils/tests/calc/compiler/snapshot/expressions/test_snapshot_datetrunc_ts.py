from __future__ import annotations

from datetime import datetime

import polars as pl
import pytest
from inline_snapshot import snapshot

from hex_sl_utils.datatype import DataType
from hex_sl_utils.dialect import Dialect

from ..snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    columns = {
        "ts": DataType.TIMESTAMP,
    }

    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            "ts",
            "truncyear(ts)",
            "truncquarter(ts)",
            "truncmonth(ts)",
            "truncweek(ts)",
            "truncweekmonday(ts)",
            "truncday(ts)",
            "trunchour(ts)",
            "truncminute(ts)",
            "truncsecond(ts)",
            "truncmillisecond(ts)",
        ]

    @classmethod
    def get_expression_input_data(cls) -> pl.DataFrame:
        df = pl.DataFrame(
            {
                "ts": [
                    datetime(2021, 1, 1, 0, 0, 0, 123456),
                    datetime(2022, 5, 15, 14, 45, 30, 456123),
                    datetime(2023, 12, 30, 18, 20, 15, 789345),
                    datetime(2024, 9, 12, 23, 59, 59, 999456),
                ]
            }
        )
        return df

    @classmethod
    def get_expected_df_from_input(
        cls, expression_input_data: pl.DataFrame, dialect: Dialect
    ) -> pl.DataFrame:
        df = expression_input_data
        expected_df = pl.DataFrame(
            {
                "row": [0, 1, 2, 3],
                "col1": df["ts"],
                "col2": df.select(pl.col("ts").dt.truncate("1y")),
                "col3": df.select(pl.col("ts").dt.truncate("1q")),
                "col4": df.select(pl.col("ts").dt.truncate("1mo")),
                "col5": df.select(
                    # Truncate to Sunday-based week
                    pl.col("ts").dt.truncate("1d")
                    - pl.duration(days=pl.col("ts").dt.weekday() % 7 + 1)
                    + pl.duration(days=1)
                ),
                "col6": df.select(pl.col("ts").dt.truncate("1w")),
                "col7": df.select(pl.col("ts").dt.truncate("1d")),
                "col8": df.select(pl.col("ts").dt.truncate("1h")),
                "col9": df.select(pl.col("ts").dt.truncate("1m")),
                "col10": df.select(pl.col("ts").dt.truncate("1s")),
                "col11": df.select(pl.col("ts").dt.truncate("1ms")),
            }
        )
        return expected_df


# Database result tests


def test_snapshot_datetrunc_ts_validate(dialect_name):
    """Test datetrunc timestamp expressions for each dialect separately."""
    dialect = Dialect.from_name(dialect_name)
    result_df = SnapshotTest.get_result_df(dialect)
    expected_df = SnapshotTest.get_expected_df(dialect)
    SnapshotTest.validate(expected_df, result_df, dialect)


@pytest.mark.database
@pytest.mark.database_local
def test_snapshot_datetrunc_ts_result():
    """Test datetrunc timestamp expressions for each dialect separately."""
    dialect_name = SnapshotTest.result_dialect
    dialect = Dialect.from_name(dialect_name)
    result_str = SnapshotTest.get_result_df_str(dialect)

    assert result_str == snapshot("""\
shape: (4, 12)
┌─────┬─────────────────┬─────────────────┬─────────────────┬─────────────────┬─────────────────┬─────────────────┬────────────────┬────────────────┬────────────────┬────────────────┬────────────────┐
│ row ┆ col1            ┆ col2            ┆ col3            ┆ col4            ┆ col5            ┆ col6            ┆ col7           ┆ col8           ┆ col9           ┆ col10          ┆ col11          │
│ --- ┆ ---             ┆ ---             ┆ ---             ┆ ---             ┆ ---             ┆ ---             ┆ ---            ┆ ---            ┆ ---            ┆ ---            ┆ ---            │
│ i32 ┆ datetime[μs]    ┆ datetime[μs]    ┆ datetime[μs]    ┆ datetime[μs]    ┆ datetime[μs]    ┆ datetime[μs]    ┆ datetime[μs]   ┆ datetime[μs]   ┆ datetime[μs]   ┆ datetime[μs]   ┆ datetime[μs]   │
╞═════╪═════════════════╪═════════════════╪═════════════════╪═════════════════╪═════════════════╪═════════════════╪════════════════╪════════════════╪════════════════╪════════════════╪════════════════╡
│ 0   ┆ 2021-01-01      ┆ 2021-01-01      ┆ 2021-01-01      ┆ 2021-01-01      ┆ 2020-12-27      ┆ 2020-12-28      ┆ 2021-01-01     ┆ 2021-01-01     ┆ 2021-01-01     ┆ 2021-01-01     ┆ 2021-01-01     │
│     ┆ 00:00:00.123456 ┆ 00:00:00        ┆ 00:00:00        ┆ 00:00:00        ┆ 00:00:00        ┆ 00:00:00        ┆ 00:00:00       ┆ 00:00:00       ┆ 00:00:00       ┆ 00:00:00       ┆ 00:00:00.123   │
│ 1   ┆ 2022-05-15      ┆ 2022-01-01      ┆ 2022-04-01      ┆ 2022-05-01      ┆ 2022-05-15      ┆ 2022-05-09      ┆ 2022-05-15     ┆ 2022-05-15     ┆ 2022-05-15     ┆ 2022-05-15     ┆ 2022-05-15     │
│     ┆ 14:45:30.456123 ┆ 00:00:00        ┆ 00:00:00        ┆ 00:00:00        ┆ 00:00:00        ┆ 00:00:00        ┆ 00:00:00       ┆ 14:00:00       ┆ 14:45:00       ┆ 14:45:30       ┆ 14:45:30.456   │
│ 2   ┆ 2023-12-30      ┆ 2023-01-01      ┆ 2023-10-01      ┆ 2023-12-01      ┆ 2023-12-24      ┆ 2023-12-25      ┆ 2023-12-30     ┆ 2023-12-30     ┆ 2023-12-30     ┆ 2023-12-30     ┆ 2023-12-30     │
│     ┆ 18:20:15.789345 ┆ 00:00:00        ┆ 00:00:00        ┆ 00:00:00        ┆ 00:00:00        ┆ 00:00:00        ┆ 00:00:00       ┆ 18:00:00       ┆ 18:20:00       ┆ 18:20:15       ┆ 18:20:15.789   │
│ 3   ┆ 2024-09-12      ┆ 2024-01-01      ┆ 2024-07-01      ┆ 2024-09-01      ┆ 2024-09-08      ┆ 2024-09-09      ┆ 2024-09-12     ┆ 2024-09-12     ┆ 2024-09-12     ┆ 2024-09-12     ┆ 2024-09-12     │
│     ┆ 23:59:59.999456 ┆ 00:00:00        ┆ 00:00:00        ┆ 00:00:00        ┆ 00:00:00        ┆ 00:00:00        ┆ 00:00:00       ┆ 23:00:00       ┆ 23:59:00       ┆ 23:59:59       ┆ 23:59:59.999   │
└─────┴─────────────────┴─────────────────┴─────────────────┴─────────────────┴─────────────────┴─────────────────┴────────────────┴────────────────┴────────────────┴────────────────┴────────────────┘\
""")


# SQL expression snapshots


def test_snapshot_datetrunc_ts_sql():
    """Snapshot directly compiled calc SQL for every supported dialect."""
    assert SnapshotTest.render_sql_snapshot() == snapshot("""\
-- === BIGQUERY ===
`ts`;
DATE_TRUNC(`ts`, YEAR);
DATE_TRUNC(`ts`, QUARTER);
DATE_TRUNC(`ts`, MONTH);
DATE_TRUNC(`ts`, WEEK);
DATE_TRUNC(`ts`, WEEK(MONDAY));
DATE_TRUNC(`ts`, DAY);
DATE_TRUNC(`ts`, HOUR);
DATE_TRUNC(`ts`, MINUTE);
DATE_TRUNC(`ts`, SECOND);
DATE_TRUNC(`ts`, MILLISECOND);

-- === CLICKHOUSE ===
"ts";
toDateTime64(dateTrunc('year', "ts"), 3);
toDateTime64(dateTrunc('quarter', "ts"), 3);
toDateTime64(dateTrunc('month', "ts"), 3);
toDateTime64(dateTrunc('week', "ts" + INTERVAL 1 day) - INTERVAL 1 day, 3);
toDateTime64(dateTrunc('week', "ts"), 3);
toDateTime64(dateTrunc('day', "ts"), 3);
dateTrunc('hour', "ts");
dateTrunc('minute', "ts");
dateTrunc('second', "ts");
dateTrunc('millisecond', "ts");

-- === DUCKDB ===
"ts";
CAST(DATE_TRUNC('YEAR', "ts") AS TIMESTAMP);
CAST(DATE_TRUNC('QUARTER', "ts") AS TIMESTAMP);
CAST(DATE_TRUNC('MONTH', "ts") AS TIMESTAMP);
CAST(DATE_TRUNC('WEEK', (
  "ts" + INTERVAL 1 day
)) - INTERVAL 1 day AS TIMESTAMP);
CAST(DATE_TRUNC('WEEK', "ts") AS TIMESTAMP);
CAST(DATE_TRUNC('DAY', "ts") AS TIMESTAMP);
DATE_TRUNC('HOUR', "ts");
DATE_TRUNC('MINUTE', "ts");
DATE_TRUNC('SECOND', "ts");
DATE_TRUNC('MILLISECOND', "ts");

-- === MSSQL ===
[ts];
DATETIME2FROMPARTS(DATEPART(year, [ts]), 1, 1, 0, 0, 0, 0, 3);
DATETIME2FROMPARTS(
  DATEPART(year, [ts]),
  FLOOR(CAST((
    DATEPART(month, [ts]) - 1
  ) AS FLOAT) / 3) * 3 + 1,
  1,
  0,
  0,
  0,
  0,
  3
);
DATETIME2FROMPARTS(DATEPART(year, [ts]), DATEPART(month, [ts]), 1, 0, 0, 0, 0, 3);
DATEADD(
  DAY,
  -DATEPART(weekday, [ts]) + 1,
  DATETIME2FROMPARTS(DATEPART(year, [ts]), DATEPART(month, [ts]), DATEPART(day, [ts]), 0, 0, 0, 0, 3)
);
DATEADD(
  DAY,
  -(
    (
      (
        DATEPART(weekday, [ts]) + 5
      ) % 7
    ) + 1
  ) + 1,
  DATETIME2FROMPARTS(DATEPART(year, [ts]), DATEPART(month, [ts]), DATEPART(day, [ts]), 0, 0, 0, 0, 3)
);
DATETIME2FROMPARTS(DATEPART(year, [ts]), DATEPART(month, [ts]), DATEPART(day, [ts]), 0, 0, 0, 0, 3);
DATETIME2FROMPARTS(
  DATEPART(year, [ts]),
  DATEPART(month, [ts]),
  DATEPART(day, [ts]),
  DATEPART(hour, [ts]),
  0,
  0,
  0,
  3
);
DATETIME2FROMPARTS(
  DATEPART(year, [ts]),
  DATEPART(month, [ts]),
  DATEPART(day, [ts]),
  DATEPART(hour, [ts]),
  DATEPART(minute, [ts]),
  0,
  0,
  3
);
DATETIME2FROMPARTS(
  DATEPART(year, [ts]),
  DATEPART(month, [ts]),
  DATEPART(day, [ts]),
  DATEPART(hour, [ts]),
  DATEPART(minute, [ts]),
  DATEPART(second, [ts]),
  0,
  3
);
DATETIME2FROMPARTS(
  DATEPART(year, [ts]),
  DATEPART(month, [ts]),
  DATEPART(day, [ts]),
  DATEPART(hour, [ts]),
  DATEPART(minute, [ts]),
  DATEPART(second, [ts]),
  DATEPART(millisecond, [ts]),
  3
);

-- === MYSQL ===
`ts`;
TIMESTAMP(CAST(DATE_FORMAT(`ts`, '%Y-01-01') AS DATE));
TIMESTAMP(
  CAST(DATE_FORMAT(`ts`, CONCAT('%Y-', (
    (
      QUARTER(`ts`) - 1
    ) * 3 + 1
  ), '-01')) AS DATE)
);
TIMESTAMP(CAST(DATE_FORMAT(`ts`, '%Y-%m-01') AS DATE));
TIMESTAMP(
  DATE_SUB(
    CAST(DATE_FORMAT(`ts`, '%Y-%m-%d') AS DATE),
    INTERVAL (DAYOFWEEK(DATE(`ts`)) - 1) DAY
  )
);
TIMESTAMP(
  DATE_SUB(CAST(DATE_FORMAT(`ts`, '%Y-%m-%d') AS DATE), INTERVAL (WEEKDAY(DATE(`ts`))) DAY)
);
TIMESTAMP(CAST(DATE_FORMAT(`ts`, '%Y-%m-%d') AS DATE));
TIMESTAMP(CAST(DATE_FORMAT(`ts`, '%Y-%m-%d %H:00:00') AS DATETIME));
TIMESTAMP(CAST(DATE_FORMAT(`ts`, '%Y-%m-%d %H:%i:00') AS DATETIME));
TIMESTAMP(CAST(DATE_FORMAT(`ts`, '%Y-%m-%d %T') AS DATETIME));
TIMESTAMP(CAST(DATE_FORMAT(`ts`, '%Y-%m-%d %T.%f') AS DATETIME(3)));

-- === POSTGRES ===
"ts";
CAST(DATE_TRUNC('YEAR', "ts") AS TIMESTAMP);
CAST(DATE_TRUNC('QUARTER', "ts") AS TIMESTAMP);
CAST(DATE_TRUNC('MONTH', "ts") AS TIMESTAMP);
CAST(DATE_TRUNC('WEEK', (
  "ts" + INTERVAL '1 day'
)) - INTERVAL '1 day' AS TIMESTAMP);
CAST(DATE_TRUNC('WEEK', "ts") AS TIMESTAMP);
CAST(DATE_TRUNC('DAY', "ts") AS TIMESTAMP);
DATE_TRUNC('HOUR', "ts");
DATE_TRUNC('MINUTE', "ts");
DATE_TRUNC('SECOND', "ts");
DATE_TRUNC('MILLISECOND', "ts");

-- === REDSHIFT ===
"ts";
DATE_TRUNC('YEAR', "ts");
DATE_TRUNC('QUARTER', "ts");
DATE_TRUNC('MONTH', "ts");
(
  DATE_TRUNC('WEEK', (
    "ts"
  ) + INTERVAL '1 day') - INTERVAL '1 day'
);
DATE_TRUNC('WEEK', "ts");
DATE_TRUNC('DAY', "ts");
DATE_TRUNC('HOUR', "ts");
DATE_TRUNC('MINUTE', "ts");
DATE_TRUNC('SECOND', "ts");
DATE_TRUNC('MILLISECOND', "ts");

-- === SNOWFLAKE ===
"ts";
DATE_TRUNC('YEAR', "ts");
DATE_TRUNC('QUARTER', "ts");
DATE_TRUNC('MONTH', "ts");
DATEADD(
  DAY,
  -DAYOFWEEKISO(DATE_TRUNC('WEEK', CAST('2012-01-08' AS DATE))) % 7,
  DATE_TRUNC(
    'WEEK',
    DATEADD(DAY, DAYOFWEEKISO(DATE_TRUNC('WEEK', CAST('2012-01-08' AS DATE))) % 7, "ts")
  )
);
DATEADD(
  DAY,
  -(
    DAYOFWEEKISO(DATE_TRUNC('WEEK', CAST('2012-01-08' AS DATE))) - 1
  ) % 7,
  DATE_TRUNC(
    'WEEK',
    DATEADD(
      DAY,
      (
        DAYOFWEEKISO(DATE_TRUNC('WEEK', CAST('2012-01-08' AS DATE))) - 1
      ) % 7,
      "ts"
    )
  )
);
DATE_TRUNC('DAY', "ts");
DATE_TRUNC('HOUR', "ts");
DATE_TRUNC('MINUTE', "ts");
DATE_TRUNC('SECOND', "ts");
DATE_TRUNC('MILLISECOND', "ts");

-- === SPARK ===
`ts`;
CAST(DATE_TRUNC('YEAR', `ts`) AS TIMESTAMP);
CAST(DATE_TRUNC('QUARTER', `ts`) AS TIMESTAMP);
CAST(DATE_TRUNC('MONTH', `ts`) AS TIMESTAMP);
CAST(DATE_ADD(DATE_TRUNC('WEEK', DATE_ADD(`ts`, 1)), -1) AS TIMESTAMP);
CAST(DATE_TRUNC('WEEK', `ts`) AS TIMESTAMP);
CAST(DATE_TRUNC('DAY', `ts`) AS TIMESTAMP);
DATE_TRUNC('HOUR', `ts`);
DATE_TRUNC('MINUTE', `ts`);
DATE_TRUNC('SECOND', `ts`);
DATE_TRUNC('MILLISECOND', `ts`);

-- === TRINO ===
"ts";
DATE_TRUNC('YEAR', "ts");
DATE_TRUNC('QUARTER', "ts");
DATE_TRUNC('MONTH', "ts");
DATE_ADD('DAY', -1, DATE_TRUNC('WEEK', DATE_ADD('DAY', 1, "ts")));
DATE_TRUNC('WEEK', "ts");
DATE_TRUNC('DAY', "ts");
DATE_TRUNC('HOUR', "ts");
DATE_TRUNC('MINUTE', "ts");
DATE_TRUNC('SECOND', "ts");
DATE_TRUNC('MILLISECOND', "ts");
""")
