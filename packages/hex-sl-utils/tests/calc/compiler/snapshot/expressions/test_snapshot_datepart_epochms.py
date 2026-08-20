from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import polars as pl
import pytest
from inline_snapshot import snapshot

from hex_sl_utils.datatype import DataType
from hex_sl_utils.dialect import Dialect

from ..snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    columns = {
        "ts": DataType.TIMESTAMP,
        "d": DataType.DATE,
        "ts_tz": DataType.TIMESTAMPTZ,
    }
    timezone = "America/New_York"

    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            "datetimetoepochms(d)",
            "datetimetoepochms(ts)",
            "datetimetoepochms(ts_tz)",
            "epochmstodatetime(datetimetoepochms(d))",
            "epochmstodatetime(datetimetoepochms(ts))",
            "epochmstodatetime(datetimetoepochms(ts_tz))",
        ]

    @classmethod
    def get_expression_input_data(cls) -> pl.DataFrame:
        ts = [
            datetime(2021, 1, 1, 0, 0, 0, 123000),
            datetime(2022, 5, 15, 14, 45, 30, 456000),
            datetime(2023, 12, 30, 18, 20, 15, 789000),
            datetime(2024, 9, 12, 23, 59, 59, 999000),
        ]

        df = pl.DataFrame(
            {
                "ts": ts,
                "d": [t.date() for t in ts],
                "ts_tz": [t.replace(tzinfo=ZoneInfo("UTC")) for t in ts],
            }
        )
        return df

    @classmethod
    def get_expected_df_from_input(
        cls, expression_input_data: pl.DataFrame, dialect: Dialect
    ) -> pl.DataFrame:
        df = expression_input_data
        timezone = "America/New_York"
        expected_df = pl.DataFrame(
            {
                "row": [0, 1, 2, 3],
                "col1": df.select(pl.col("d").dt.timestamp("ms")),
                "col2": df.select(pl.col("ts").dt.timestamp("ms")),
                "col3": df.select(pl.col("ts_tz").dt.timestamp("ms")),
                "col4": df.select(
                    pl.from_epoch(pl.col("d").dt.timestamp("ms"), time_unit="ms")
                    .dt.replace_time_zone("UTC")
                    .dt.convert_time_zone(timezone),
                ),
                "col5": df.select(
                    pl.from_epoch(pl.col("ts").dt.timestamp("ms"), time_unit="ms")
                    .dt.replace_time_zone("UTC")
                    .dt.convert_time_zone(timezone)
                ),
                "col6": df.select(
                    pl.from_epoch(pl.col("ts_tz").dt.timestamp("ms"), time_unit="ms")
                    .dt.replace_time_zone("UTC")
                    .dt.convert_time_zone(timezone)
                ),
            }
        )
        return expected_df


# Database result tests


def test_snapshot_datepart_epochms_validate(dialect_name):
    """Test datepart epochms expressions for each dialect separately."""
    dialect = Dialect.from_name(dialect_name)
    result_df = SnapshotTest.get_result_df(dialect, timezone="America/New_York")
    expected_df = SnapshotTest.get_expected_df(dialect)
    SnapshotTest.validate(expected_df, result_df, dialect)


@pytest.mark.database
@pytest.mark.database_local
def test_snapshot_datepart_epochms_result():
    """Test datepart epochms expressions for each dialect separately."""
    dialect_name = SnapshotTest.result_dialect
    dialect = Dialect.from_name(dialect_name)
    result_str = SnapshotTest.get_result_df_str(dialect, timezone="America/New_York")

    assert result_str == snapshot("""\
shape: (4, 7)
┌─────┬───────────────┬───────────────┬───────────────┬────────────────────────────────┬────────────────────────────────┬────────────────────────────────┐
│ row ┆ col1          ┆ col2          ┆ col3          ┆ col4                           ┆ col5                           ┆ col6                           │
│ --- ┆ ---           ┆ ---           ┆ ---           ┆ ---                            ┆ ---                            ┆ ---                            │
│ i32 ┆ i64           ┆ i64           ┆ i64           ┆ datetime[μs, America/New_York] ┆ datetime[μs, America/New_York] ┆ datetime[μs, America/New_York] │
╞═════╪═══════════════╪═══════════════╪═══════════════╪════════════════════════════════╪════════════════════════════════╪════════════════════════════════╡
│ 0   ┆ 1609459200000 ┆ 1609459200123 ┆ 1609459200123 ┆ 2020-12-31 19:00:00 EST        ┆ 2020-12-31 19:00:00.123 EST    ┆ 2020-12-31 19:00:00.123 EST    │
│ 1   ┆ 1652572800000 ┆ 1652625930456 ┆ 1652625930456 ┆ 2022-05-14 20:00:00 EDT        ┆ 2022-05-15 10:45:30.456 EDT    ┆ 2022-05-15 10:45:30.456 EDT    │
│ 2   ┆ 1703894400000 ┆ 1703960415789 ┆ 1703960415789 ┆ 2023-12-29 19:00:00 EST        ┆ 2023-12-30 13:20:15.789 EST    ┆ 2023-12-30 13:20:15.789 EST    │
│ 3   ┆ 1726099200000 ┆ 1726185599999 ┆ 1726185599999 ┆ 2024-09-11 20:00:00 EDT        ┆ 2024-09-12 19:59:59.999 EDT    ┆ 2024-09-12 19:59:59.999 EDT    │
└─────┴───────────────┴───────────────┴───────────────┴────────────────────────────────┴────────────────────────────────┴────────────────────────────────┘\
""")


# SQL expression snapshots


def test_snapshot_datepart_epochms_sql():
    """Snapshot directly compiled calc SQL for every supported dialect."""
    assert SnapshotTest.render_sql_snapshot() == snapshot("""\
-- === BIGQUERY ===
IF(NOT `d` IS NULL, UNIX_DATE(`d`) * 86400000, NULL);
IF(NOT `ts` IS NULL, UNIX_MILLIS(TIMESTAMP(`ts`)), NULL);
IF(NOT `ts_tz` IS NULL, UNIX_MILLIS(TIMESTAMP(DATETIME(`ts_tz`, 'UTC'))), NULL);
timestamp_millis(CAST(trunc(IF(NOT `d` IS NULL, UNIX_DATE(`d`) * 86400000, NULL)) AS INT64));
timestamp_millis(CAST(trunc(IF(NOT `ts` IS NULL, UNIX_MILLIS(TIMESTAMP(`ts`)), NULL)) AS INT64));
timestamp_millis(
  CAST(trunc(IF(NOT `ts_tz` IS NULL, UNIX_MILLIS(TIMESTAMP(DATETIME(`ts_tz`, 'UTC'))), NULL)) AS INT64)
);

-- === CLICKHOUSE ===
toRelativeSecondNum("d") * 1000;
(
  toUnixTimestamp64Milli("ts")
);
(
  toUnixTimestamp64Milli("ts_tz")
);
toDateTime64((
  toRelativeSecondNum("d") * 1000
) / 1000, 3, 'UTC');
toDateTime64((
  (
    toUnixTimestamp64Milli("ts")
  )
) / 1000, 3, 'UTC');
toDateTime64((
  (
    toUnixTimestamp64Milli("ts_tz")
  )
) / 1000, 3, 'UTC');

-- === DUCKDB ===
CAST(EPOCH_MS("d") AS BIGINT);
CAST(EPOCH_MS("ts") AS BIGINT);
CAST(EPOCH_MS("ts_tz" AT TIME ZONE 'UTC') AS BIGINT);
EPOCH_MS(CAST(CAST(EPOCH_MS("d") AS BIGINT) AS BIGINT)) AT TIME ZONE 'UTC';
EPOCH_MS(CAST(CAST(EPOCH_MS("ts") AS BIGINT) AS BIGINT)) AT TIME ZONE 'UTC';
EPOCH_MS(CAST(CAST(EPOCH_MS("ts_tz" AT TIME ZONE 'UTC') AS BIGINT) AS BIGINT)) AT TIME ZONE 'UTC';

-- === MSSQL ===
CAST(DATEDIFF(SECOND, CAST('1970-01-01 00:00:00' AS DATETIME2), CAST([d] AS DATETIME2)) AS BIGINT) * 1000;
(
  (
    CAST(DATEDIFF(SECOND, CAST('1970-01-01 00:00:00' AS DATETIME2), CAST([ts] AS DATETIME2)) AS BIGINT) * 1000
  ) + DATEPART(millisecond, [ts])
);
(
  (
    CAST(DATEDIFF(
      SECOND,
      CAST('1970-01-01 00:00:00' AS DATETIME2),
      CAST([ts_tz] AT TIME ZONE 'UTC' AS DATETIME2)
    ) AS BIGINT) * 1000
  ) + DATEPART(millisecond, [ts_tz] AT TIME ZONE 'UTC')
);
DATEADD(
  MICROSECOND,
  (
    (
      CAST(DATEDIFF(SECOND, CAST('1970-01-01 00:00:00' AS DATETIME2), CAST([d] AS DATETIME2)) AS BIGINT) * 1000
    ) % 1000
  ) * 1000,
  CAST(DATEADD(
    s,
    CAST(CAST(DATEDIFF(SECOND, CAST('1970-01-01 00:00:00' AS DATETIME2), CAST([d] AS DATETIME2)) AS BIGINT) * 1000 AS FLOAT) / 1000,
    '1970-01-01 00:00:00'
  ) AS DATETIME2)
) AT TIME ZONE 'UTC';
DATEADD(
  MICROSECOND,
  (
    (
      (
        (
          CAST(DATEDIFF(SECOND, CAST('1970-01-01 00:00:00' AS DATETIME2), CAST([ts] AS DATETIME2)) AS BIGINT) * 1000
        ) + DATEPART(millisecond, [ts])
      )
    ) % 1000
  ) * 1000,
  CAST(DATEADD(
    s,
    CAST((
      (
        CAST(DATEDIFF(SECOND, CAST('1970-01-01 00:00:00' AS DATETIME2), CAST([ts] AS DATETIME2)) AS BIGINT) * 1000
      ) + DATEPART(millisecond, [ts])
    ) AS FLOAT) / 1000,
    '1970-01-01 00:00:00'
  ) AS DATETIME2)
) AT TIME ZONE 'UTC';
DATEADD(
  MICROSECOND,
  (
    (
      (
        (
          CAST(DATEDIFF(
            SECOND,
            CAST('1970-01-01 00:00:00' AS DATETIME2),
            CAST([ts_tz] AT TIME ZONE 'UTC' AS DATETIME2)
          ) AS BIGINT) * 1000
        ) + DATEPART(millisecond, [ts_tz] AT TIME ZONE 'UTC')
      )
    ) % 1000
  ) * 1000,
  CAST(DATEADD(
    s,
    CAST((
      (
        CAST(DATEDIFF(
          SECOND,
          CAST('1970-01-01 00:00:00' AS DATETIME2),
          CAST([ts_tz] AT TIME ZONE 'UTC' AS DATETIME2)
        ) AS BIGINT) * 1000
      ) + DATEPART(millisecond, [ts_tz] AT TIME ZONE 'UTC')
    ) AS FLOAT) / 1000,
    '1970-01-01 00:00:00'
  ) AS DATETIME2)
) AT TIME ZONE 'UTC';

-- === MYSQL ===
FLOOR(UNIX_TIMESTAMP(`d`) * 1000);
FLOOR(UNIX_TIMESTAMP(`ts`) * 1000);
FLOOR(UNIX_TIMESTAMP(CAST(CONVERT_TZ(`ts_tz`, 'UTC', 'UTC') AS DATETIME(3))) * 1000);
FROM_UNIXTIME((
  FLOOR(UNIX_TIMESTAMP(`d`) * 1000)
) / 1000);
FROM_UNIXTIME((
  FLOOR(UNIX_TIMESTAMP(`ts`) * 1000)
) / 1000);
FROM_UNIXTIME(
  (
    FLOOR(UNIX_TIMESTAMP(CAST(CONVERT_TZ(`ts_tz`, 'UTC', 'UTC') AS DATETIME(3))) * 1000)
  ) / 1000
);

-- === POSTGRES ===
CAST(FLOOR(EXTRACT('epoch' FROM "d") * 1000) AS BIGINT);
CAST(FLOOR(EXTRACT('epoch' FROM "ts") * 1000) AS BIGINT);
CAST(FLOOR(EXTRACT('epoch' FROM "ts_tz" AT TIME ZONE 'UTC') * 1000) AS BIGINT);
TO_TIMESTAMP(
  CAST(CAST(FLOOR(EXTRACT('epoch' FROM "d") * 1000) AS BIGINT) AS DOUBLE PRECISION) / 1000
);
TO_TIMESTAMP(
  CAST(CAST(FLOOR(EXTRACT('epoch' FROM "ts") * 1000) AS BIGINT) AS DOUBLE PRECISION) / 1000
);
TO_TIMESTAMP(
  CAST(CAST(FLOOR(EXTRACT('epoch' FROM "ts_tz" AT TIME ZONE 'UTC') * 1000) AS BIGINT) AS DOUBLE PRECISION) / 1000
);

-- === REDSHIFT ===
CAST(EXTRACT('epoch' FROM "d") AS BIGINT) * 1000;
(
  (
    CAST(EXTRACT('millisecond' FROM "ts") AS BIGINT)
  ) + (
    CAST(EXTRACT('epoch' FROM "ts") AS BIGINT) * 1000
  )
);
(
  (
    CAST(EXTRACT('millisecond' FROM "ts_tz" AT TIME ZONE 'UTC') AS BIGINT)
  ) + (
    CAST(EXTRACT('epoch' FROM "ts_tz" AT TIME ZONE 'UTC') AS BIGINT) * 1000
  )
);
(
  CAST('epoch' AS TIMESTAMP) + (
    (
      CAST((
        CAST(EXTRACT('epoch' FROM "d") AS BIGINT) * 1000
      ) AS DOUBLE PRECISION) / 1000
    ) * INTERVAL '1 SECOND'
  )
);
(
  CAST('epoch' AS TIMESTAMP) + (
    (
      CAST((
        (
          (
            CAST(EXTRACT('millisecond' FROM "ts") AS BIGINT)
          ) + (
            CAST(EXTRACT('epoch' FROM "ts") AS BIGINT) * 1000
          )
        )
      ) AS DOUBLE PRECISION) / 1000
    ) * INTERVAL '1 SECOND'
  )
);
(
  CAST('epoch' AS TIMESTAMP) + (
    (
      CAST((
        (
          (
            CAST(EXTRACT('millisecond' FROM "ts_tz" AT TIME ZONE 'UTC') AS BIGINT)
          ) + (
            CAST(EXTRACT('epoch' FROM "ts_tz" AT TIME ZONE 'UTC') AS BIGINT) * 1000
          )
        )
      ) AS DOUBLE PRECISION) / 1000
    ) * INTERVAL '1 SECOND'
  )
);

-- === SNOWFLAKE ===
DATE_PART('epoch_second', "d") * 1000;
DATE_PART('epoch_millisecond', "ts");
DATE_PART('epoch_millisecond', CONVERT_TIMEZONE('UTC', "ts_tz"));
TO_TIMESTAMP_TZ(DATE_PART('epoch_second', "d") * 1000, 3);
TO_TIMESTAMP_TZ(DATE_PART('epoch_millisecond', "ts"), 3);
TO_TIMESTAMP_TZ(DATE_PART('epoch_millisecond', CONVERT_TIMEZONE('UTC', "ts_tz")), 3);

-- === SPARK ===
(
  UNIX_TIMESTAMP(FROM_UTC_TIMESTAMP(CAST(`d` AS TIMESTAMP), CURRENT_TIMEZONE())) * 1000 + CAST(EXTRACT(seconds FROM `d`) % 1 * 1000 AS BIGINT)
);
(
  UNIX_TIMESTAMP(FROM_UTC_TIMESTAMP(CAST(`ts` AS TIMESTAMP), CURRENT_TIMEZONE())) * 1000 + CAST(EXTRACT(seconds FROM `ts`) % 1 * 1000 AS BIGINT)
);
(
  UNIX_TIMESTAMP(`ts_tz`) * 1000 + CAST(EXTRACT(seconds FROM `ts_tz`) % 1 * 1000 AS BIGINT)
);
DATE_ADD(
  MILLISECOND,
  (
    (
      UNIX_TIMESTAMP(FROM_UTC_TIMESTAMP(CAST(`d` AS TIMESTAMP), CURRENT_TIMEZONE())) * 1000 + CAST(EXTRACT(seconds FROM `d`) % 1 * 1000 AS BIGINT)
    )
  ) % 1000,
  TO_UTC_TIMESTAMP(
    CAST(FROM_UNIXTIME(
      (
        (
          UNIX_TIMESTAMP(FROM_UTC_TIMESTAMP(CAST(`d` AS TIMESTAMP), CURRENT_TIMEZONE())) * 1000 + CAST(EXTRACT(seconds FROM `d`) % 1 * 1000 AS BIGINT)
        )
      ) / 1000
    ) AS TIMESTAMP),
    CURRENT_TIMEZONE()
  )
);
DATE_ADD(
  MILLISECOND,
  (
    (
      UNIX_TIMESTAMP(FROM_UTC_TIMESTAMP(CAST(`ts` AS TIMESTAMP), CURRENT_TIMEZONE())) * 1000 + CAST(EXTRACT(seconds FROM `ts`) % 1 * 1000 AS BIGINT)
    )
  ) % 1000,
  TO_UTC_TIMESTAMP(
    CAST(FROM_UNIXTIME(
      (
        (
          UNIX_TIMESTAMP(FROM_UTC_TIMESTAMP(CAST(`ts` AS TIMESTAMP), CURRENT_TIMEZONE())) * 1000 + CAST(EXTRACT(seconds FROM `ts`) % 1 * 1000 AS BIGINT)
        )
      ) / 1000
    ) AS TIMESTAMP),
    CURRENT_TIMEZONE()
  )
);
DATE_ADD(
  MILLISECOND,
  (
    (
      UNIX_TIMESTAMP(`ts_tz`) * 1000 + CAST(EXTRACT(seconds FROM `ts_tz`) % 1 * 1000 AS BIGINT)
    )
  ) % 1000,
  TO_UTC_TIMESTAMP(
    CAST(FROM_UNIXTIME(
      (
        (
          UNIX_TIMESTAMP(`ts_tz`) * 1000 + CAST(EXTRACT(seconds FROM `ts_tz`) % 1 * 1000 AS BIGINT)
        )
      ) / 1000
    ) AS TIMESTAMP),
    CURRENT_TIMEZONE()
  )
);

-- === TRINO ===
CAST(FLOOR(TO_UNIXTIME("d") * 1000) AS BIGINT);
CAST(FLOOR(TO_UNIXTIME("ts") * 1000) AS BIGINT);
CAST(FLOOR(TO_UNIXTIME(AT_TIMEZONE("ts_tz", 'UTC')) * 1000) AS BIGINT);
WITH_TIMEZONE(
  DATE_ADD(
    'MILLISECOND',
    (
      (
        CAST(FLOOR(TO_UNIXTIME("d") * 1000) AS BIGINT)
      ) % 1000
    ),
    CAST(FROM_UNIXTIME(
      FLOOR(
        CAST(CAST(CAST(FLOOR(TO_UNIXTIME("d") * 1000) AS BIGINT) AS BIGINT) AS DOUBLE) / 1000
      )
    ) AS TIMESTAMP)
  ),
  'UTC'
);
WITH_TIMEZONE(
  DATE_ADD(
    'MILLISECOND',
    (
      (
        CAST(FLOOR(TO_UNIXTIME("ts") * 1000) AS BIGINT)
      ) % 1000
    ),
    CAST(FROM_UNIXTIME(
      FLOOR(
        CAST(CAST(CAST(FLOOR(TO_UNIXTIME("ts") * 1000) AS BIGINT) AS BIGINT) AS DOUBLE) / 1000
      )
    ) AS TIMESTAMP)
  ),
  'UTC'
);
WITH_TIMEZONE(
  DATE_ADD(
    'MILLISECOND',
    (
      (
        CAST(FLOOR(TO_UNIXTIME(AT_TIMEZONE("ts_tz", 'UTC')) * 1000) AS BIGINT)
      ) % 1000
    ),
    CAST(FROM_UNIXTIME(
      FLOOR(
        CAST(CAST(CAST(FLOOR(TO_UNIXTIME(AT_TIMEZONE("ts_tz", 'UTC')) * 1000) AS BIGINT) AS BIGINT) AS DOUBLE) / 1000
      )
    ) AS TIMESTAMP)
  ),
  'UTC'
);
""")
