from __future__ import annotations

from datetime import date, datetime

import polars as pl
import pytest
from inline_snapshot import snapshot

from hex_sl_utils.datatype import DataType
from hex_sl_utils.dialect import Dialect

from ..snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    columns = {
        "str_int": DataType.STRING,
        "str_float": DataType.STRING,
        "bool_col": DataType.BOOLEAN,
        "date_col": DataType.DATE,
        "timestamp_col": DataType.TIMESTAMP,
        "int_col": DataType.NUMBER,
        "float_col": DataType.NUMBER,
        "str_date": DataType.STRING,
        "str_datetime": DataType.STRING,
        "epoch_ms": DataType.NUMBER,
    }

    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        """Return calc expressions to test."""
        return [
            # _chart_toNumber tests
            "_chart_toNumber(str_int)",  # String to number
            "_chart_toNumber(str_float)",  # String float to number
            "_chart_toNumber(bool_col)",  # Boolean to number (1/0)
            "_chart_toNumber(date_col)",  # Date to epoch ms
            "_chart_toNumber(timestamp_col)",  # Timestamp to epoch ms
            "_chart_toNumber(int_col)",  # Number to number (no-op)
            "_chart_toNumber(float_col)",  # Float to float (no-op)
            # _chart_toDatetime tests
            "_chart_toDatetime(str_date)",  # String to datetime
            "_chart_toDatetime(str_datetime)",  # String datetime to datetime
            "_chart_toDatetime(epoch_ms)",  # Number to datetime
            "_chart_toDatetime(bool_col)",  # Boolean to datetime (via epoch)
            "_chart_toDatetime(date_col)",  # Date to timestamp
            "_chart_toDatetime(timestamp_col)",  # Timestamp to timestamp (no-op)
            # Combined tests
            "_chart_toNumber(_chart_toDatetime(str_date))",  # String -> datetime -> number
            "_chart_toDatetime(_chart_toNumber(bool_col))",  # Boolean -> number -> datetime
        ]

    @classmethod
    def get_expression_input_data(cls) -> pl.DataFrame:
        """Create test data for all internal function tests."""
        return pl.DataFrame(
            {
                # String columns for testing conversions
                "str_int": ["123", "456", "-789", "0"],
                "str_float": ["123.45", "-67.89", "0.0", "999.999"],
                "str_invalid": ["abc", "12x34", "", "null"],
                "str_date": ["2023-01-01", "2023-06-15", "2023-12-31", "2024-02-29"],
                "str_datetime": [
                    "2023-01-01 00:00:00",
                    "2023-06-15 12:30:45",
                    "2023-12-31 23:59:59",
                    "2024-02-29 06:00:00",
                ],
                # Boolean column
                "bool_col": [True, False, True, False],
                # Numeric columns
                "int_col": [1, 2, 3, -4],
                "float_col": [1.5, 2.5, -3.5, 0.0],
                "epoch_ms": [
                    1672531200000,  # 2023-01-01 00:00:00 UTC
                    1686835845000,  # 2023-06-15 12:30:45 UTC
                    1704067199000,  # 2023-12-31 23:59:59 UTC
                    0,  # Unix epoch
                ],
                # Date/time columns
                "date_col": [
                    date(2023, 1, 1),
                    date(2023, 6, 15),
                    date(2023, 12, 31),
                    date(2024, 2, 29),
                ],
                "timestamp_col": [
                    datetime(2023, 1, 1, 0, 0, 0),
                    datetime(2023, 6, 15, 12, 30, 45),
                    datetime(2023, 12, 31, 23, 59, 59),
                    datetime(2024, 2, 29, 6, 0, 0),
                ],
            }
        )

    @classmethod
    def get_expected_df_from_input(
        cls, expression_input_data: pl.DataFrame, dialect: Dialect
    ) -> pl.DataFrame:
        """Calculate expected results using polars."""
        from hex_sl_utils.dialect.clickhouse import ClickHouse

        df = expression_input_data

        # Pre-compute expected values using polars expressions
        col1 = df["str_int"].cast(pl.Float64, strict=False)
        col2 = df["str_float"].cast(pl.Float64, strict=False)
        col3 = df["bool_col"].cast(pl.Int32)
        col4 = df["date_col"].cast(pl.Datetime("ms")).dt.epoch("ms")
        col5 = df["timestamp_col"].dt.epoch("ms")
        col6 = df["int_col"]
        col7 = df["float_col"]

        # Handle dialect-specific datetime precision
        if isinstance(dialect, ClickHouse):
            # ClickHouse returns nanosecond precision with UTC timezone
            col8 = (
                df["str_date"]
                .str.strptime(pl.Date, "%Y-%m-%d", strict=False)
                .cast(pl.Datetime("ns"))
                .dt.replace_time_zone("UTC")
            )
            col9 = (
                df["str_datetime"]
                .str.strptime(pl.Datetime("ns"), "%Y-%m-%d %H:%M:%S", strict=False)
                .dt.replace_time_zone("UTC")
            )
        else:
            col8 = (
                df["str_date"]
                .str.strptime(pl.Date, "%Y-%m-%d", strict=False)
                .cast(pl.Datetime("ms"))
            )
            col9 = df["str_datetime"].str.strptime(
                pl.Datetime("ms"), "%Y-%m-%d %H:%M:%S", strict=False
            )
        col10 = (
            pl.from_epoch(df["epoch_ms"], time_unit="ms")
            .dt.replace_time_zone("UTC")
            .dt.cast_time_unit("ms")
        )
        col11 = (
            pl.from_epoch(df["bool_col"].cast(pl.Int32), time_unit="ms")
            .dt.replace_time_zone("UTC")
            .dt.cast_time_unit("ms")
        )
        col12 = df["date_col"].cast(pl.Datetime("ms"))
        col13 = df["timestamp_col"]

        # Combined operations
        col14 = (
            df["str_date"]
            .str.strptime(pl.Date, "%Y-%m-%d", strict=False)
            .cast(pl.Datetime("ms"))
            .dt.epoch("ms")
        )
        col15 = (
            pl.from_epoch(df["bool_col"].cast(pl.Int32), time_unit="ms")
            .dt.replace_time_zone("UTC")
            .dt.cast_time_unit("ms")
        )

        expected_df = pl.DataFrame(
            {
                "row": [0, 1, 2, 3],
                "col1": col1,
                "col2": col2,
                "col3": col3,
                "col4": col4,
                "col5": col5,
                "col6": col6,
                "col7": col7,
                "col8": col8,
                "col9": col9,
                "col10": col10,
                "col11": col11,
                "col12": col12,
                "col13": col13,
                "col14": col14,
                "col15": col15,
            }
        )

        return expected_df


# Database result tests


def test_snapshot_internal_funcs_validate(dialect_name):
    """Test internal functions validation for each dialect."""
    dialect = Dialect.from_name(dialect_name)
    result_df = SnapshotTest.get_result_df(dialect)
    expected_df = SnapshotTest.get_expected_df(dialect)
    SnapshotTest.validate(expected_df, result_df, dialect)


@pytest.mark.database
@pytest.mark.database_local
def test_snapshot_internal_funcs_result():
    """Test internal functions result for duckdb."""
    dialect_name = SnapshotTest.result_dialect
    dialect = Dialect.from_name(dialect_name)
    result_str = SnapshotTest.get_result_df_str(dialect)

    assert result_str == snapshot("""\
shape: (4, 16)
┌─────┬────────┬─────────┬──────┬──────────────┬──────────────┬──────┬──────────────┬──────────────┬──────────────┬──────────────┬─────────────┬─────────────┬─────────────┬─────────────┬─────────────┐
│ row ┆ col1   ┆ col2    ┆ col3 ┆ col4         ┆ col5         ┆ col6 ┆ col7         ┆ col8         ┆ col9         ┆ col10        ┆ col11       ┆ col12       ┆ col13       ┆ col14       ┆ col15       │
│ --- ┆ ---    ┆ ---     ┆ ---  ┆ ---          ┆ ---          ┆ ---  ┆ ---          ┆ ---          ┆ ---          ┆ ---          ┆ ---         ┆ ---         ┆ ---         ┆ ---         ┆ ---         │
│ i32 ┆ f64    ┆ f64     ┆ i32  ┆ i64          ┆ i64          ┆ i32  ┆ decimal[2,1] ┆ datetime[μs] ┆ datetime[μs] ┆ datetime[μs, ┆ datetime[μs ┆ datetime[μs ┆ datetime[μs ┆ i64         ┆ datetime[μs │
│     ┆        ┆         ┆      ┆              ┆              ┆      ┆              ┆              ┆              ┆ UTC]         ┆ , UTC]      ┆ ]           ┆ ]           ┆             ┆ , UTC]      │
╞═════╪════════╪═════════╪══════╪══════════════╪══════════════╪══════╪══════════════╪══════════════╪══════════════╪══════════════╪═════════════╪═════════════╪═════════════╪═════════════╪═════════════╡
│ 0   ┆ 123.0  ┆ 123.45  ┆ 1    ┆ 167253120000 ┆ 167253120000 ┆ 1    ┆ 1.5          ┆ 2023-01-01   ┆ 2023-01-01   ┆ 2023-01-01   ┆ 1970-01-01  ┆ 2023-01-01  ┆ 2023-01-01  ┆ 16725312000 ┆ 1970-01-01  │
│     ┆        ┆         ┆      ┆ 0            ┆ 0            ┆      ┆              ┆ 00:00:00     ┆ 00:00:00     ┆ 00:00:00 UTC ┆ 00:00:00.00 ┆ 00:00:00    ┆ 00:00:00    ┆ 00          ┆ 00:00:00.00 │
│     ┆        ┆         ┆      ┆              ┆              ┆      ┆              ┆              ┆              ┆              ┆ 1 UTC       ┆             ┆             ┆             ┆ 1 UTC       │
│ 1   ┆ 456.0  ┆ -67.89  ┆ 0    ┆ 168678720000 ┆ 168683224500 ┆ 2    ┆ 2.5          ┆ 2023-06-15   ┆ 2023-06-15   ┆ 2023-06-15   ┆ 1970-01-01  ┆ 2023-06-15  ┆ 2023-06-15  ┆ 16867872000 ┆ 1970-01-01  │
│     ┆        ┆         ┆      ┆ 0            ┆ 0            ┆      ┆              ┆ 00:00:00     ┆ 12:30:45     ┆ 13:30:45 UTC ┆ 00:00:00    ┆ 00:00:00    ┆ 12:30:45    ┆ 00          ┆ 00:00:00    │
│     ┆        ┆         ┆      ┆              ┆              ┆      ┆              ┆              ┆              ┆              ┆ UTC         ┆             ┆             ┆             ┆ UTC         │
│ 2   ┆ -789.0 ┆ 0.0     ┆ 1    ┆ 170398080000 ┆ 170406719900 ┆ 3    ┆ -3.5         ┆ 2023-12-31   ┆ 2023-12-31   ┆ 2023-12-31   ┆ 1970-01-01  ┆ 2023-12-31  ┆ 2023-12-31  ┆ 17039808000 ┆ 1970-01-01  │
│     ┆        ┆         ┆      ┆ 0            ┆ 0            ┆      ┆              ┆ 00:00:00     ┆ 23:59:59     ┆ 23:59:59 UTC ┆ 00:00:00.00 ┆ 00:00:00    ┆ 23:59:59    ┆ 00          ┆ 00:00:00.00 │
│     ┆        ┆         ┆      ┆              ┆              ┆      ┆              ┆              ┆              ┆              ┆ 1 UTC       ┆             ┆             ┆             ┆ 1 UTC       │
│ 3   ┆ 0.0    ┆ 999.999 ┆ 0    ┆ 170916480000 ┆ 170918640000 ┆ -4   ┆ 0.0          ┆ 2024-02-29   ┆ 2024-02-29   ┆ 1970-01-01   ┆ 1970-01-01  ┆ 2024-02-29  ┆ 2024-02-29  ┆ 17091648000 ┆ 1970-01-01  │
│     ┆        ┆         ┆      ┆ 0            ┆ 0            ┆      ┆              ┆ 00:00:00     ┆ 06:00:00     ┆ 00:00:00 UTC ┆ 00:00:00    ┆ 00:00:00    ┆ 06:00:00    ┆ 00          ┆ 00:00:00    │
│     ┆        ┆         ┆      ┆              ┆              ┆      ┆              ┆              ┆              ┆              ┆ UTC         ┆             ┆             ┆             ┆ UTC         │
└─────┴────────┴─────────┴──────┴──────────────┴──────────────┴──────┴──────────────┴──────────────┴──────────────┴──────────────┴─────────────┴─────────────┴─────────────┴─────────────┴─────────────┘\
""")


# SQL expression snapshots


def test_snapshot_internal_funcs_sql():
    """Snapshot directly compiled calc SQL for every supported dialect."""
    assert SnapshotTest.render_sql_snapshot() == snapshot("""\
-- === BIGQUERY ===
SAFE_CAST(`str_int` AS FLOAT64);
SAFE_CAST(`str_float` AS FLOAT64);
CASE WHEN `bool_col` THEN 1 ELSE 0 END;
IF(NOT `date_col` IS NULL, UNIX_DATE(`date_col`) * 86400000, NULL);
IF(NOT `timestamp_col` IS NULL, UNIX_MILLIS(TIMESTAMP(`timestamp_col`)), NULL);
`int_col`;
`float_col`;
SAFE_CAST(`str_date` AS DATETIME);
SAFE_CAST(`str_datetime` AS DATETIME);
timestamp_millis(CAST(trunc(`epoch_ms`) AS INT64));
timestamp_millis(CAST(trunc(CASE WHEN `bool_col` THEN 1 ELSE 0 END) AS INT64));
CAST(`date_col` AS DATETIME);
`timestamp_col`;
IF(
  NOT SAFE_CAST(`str_date` AS DATETIME) IS NULL,
  UNIX_MILLIS(TIMESTAMP(SAFE_CAST(`str_date` AS DATETIME))),
  NULL
);
timestamp_millis(CAST(trunc(CASE WHEN `bool_col` THEN 1 ELSE 0 END) AS INT64));

-- === CLICKHOUSE ===
accurateCastOrNull("str_int", 'Nullable(Float64)');
accurateCastOrNull("str_float", 'Nullable(Float64)');
CASE WHEN "bool_col" THEN 1 ELSE 0 END;
toRelativeSecondNum("date_col") * 1000;
(
  toUnixTimestamp64Milli("timestamp_col")
);
"int_col";
"float_col";
parseDateTime64BestEffortOrNull("str_date", 3, 'UTC');
parseDateTime64BestEffortOrNull("str_datetime", 3, 'UTC');
toDateTime64((
  "epoch_ms"
) / 1000, 3, 'UTC');
toDateTime64((
  CASE WHEN "bool_col" THEN 1 ELSE 0 END
) / 1000, 3, 'UTC');
toDateTime64("date_col", 3);
"timestamp_col";
(
  toUnixTimestamp64Milli(parseDateTime64BestEffortOrNull("str_date", 3, 'UTC'))
);
toDateTime64((
  CASE WHEN "bool_col" THEN 1 ELSE 0 END
) / 1000, 3, 'UTC');

-- === DUCKDB ===
TRY_CAST("str_int" AS DOUBLE);
TRY_CAST("str_float" AS DOUBLE);
CASE WHEN "bool_col" THEN 1 ELSE 0 END;
CAST(EPOCH_MS("date_col") AS BIGINT);
CAST(EPOCH_MS("timestamp_col") AS BIGINT);
"int_col";
"float_col";
TRY_CAST(TRY_STRPTIME(
  "str_date",
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
) AS TIMESTAMP);
TRY_CAST(TRY_STRPTIME(
  "str_datetime",
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
) AS TIMESTAMP);
EPOCH_MS(CAST("epoch_ms" AS BIGINT)) AT TIME ZONE 'UTC';
EPOCH_MS(CAST(CASE WHEN "bool_col" THEN 1 ELSE 0 END AS BIGINT)) AT TIME ZONE 'UTC';
CAST("date_col" AS TIMESTAMP);
"timestamp_col";
CAST(EPOCH_MS(
  TRY_CAST(TRY_STRPTIME(
    "str_date",
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
  ) AS TIMESTAMP)
) AS BIGINT);
EPOCH_MS(CAST(CASE WHEN "bool_col" THEN 1 ELSE 0 END AS BIGINT)) AT TIME ZONE 'UTC';

-- === MSSQL ===
TRY_CAST([str_int] AS FLOAT);
TRY_CAST([str_float] AS FLOAT);
CASE WHEN [bool_col] <> 0 THEN 1 ELSE 0 END;
CAST(DATEDIFF(SECOND, CAST('1970-01-01 00:00:00' AS DATETIME2), CAST([date_col] AS DATETIME2)) AS BIGINT) * 1000;
(
  (
    CAST(DATEDIFF(SECOND, CAST('1970-01-01 00:00:00' AS DATETIME2), CAST([timestamp_col] AS DATETIME2)) AS BIGINT) * 1000
  ) + DATEPART(millisecond, [timestamp_col])
);
[int_col];
[float_col];
TRY_CAST([str_date] AS DATETIME2);
TRY_CAST([str_datetime] AS DATETIME2);
DATEADD(
  MICROSECOND,
  (
    (
      [epoch_ms]
    ) % 1000
  ) * 1000,
  CAST(DATEADD(s, CAST([epoch_ms] AS FLOAT) / 1000, '1970-01-01 00:00:00') AS DATETIME2)
) AT TIME ZONE 'UTC';
DATEADD(
  MICROSECOND,
  (
    (
      CASE WHEN [bool_col] <> 0 THEN 1 ELSE 0 END
    ) % 1000
  ) * 1000,
  CAST(DATEADD(
    s,
    CAST(CASE WHEN [bool_col] <> 0 THEN 1 ELSE 0 END AS FLOAT) / 1000,
    '1970-01-01 00:00:00'
  ) AS DATETIME2)
) AT TIME ZONE 'UTC';
CAST([date_col] AS DATETIME2);
[timestamp_col];
(
  (
    CAST(DATEDIFF(
      SECOND,
      CAST('1970-01-01 00:00:00' AS DATETIME2),
      CAST(TRY_CAST([str_date] AS DATETIME2) AS DATETIME2)
    ) AS BIGINT) * 1000
  ) + DATEPART(millisecond, TRY_CAST([str_date] AS DATETIME2))
);
DATEADD(
  MICROSECOND,
  (
    (
      CASE WHEN [bool_col] <> 0 THEN 1 ELSE 0 END
    ) % 1000
  ) * 1000,
  CAST(DATEADD(
    s,
    CAST(CASE WHEN [bool_col] <> 0 THEN 1 ELSE 0 END AS FLOAT) / 1000,
    '1970-01-01 00:00:00'
  ) AS DATETIME2)
) AT TIME ZONE 'UTC';

-- === MYSQL ===
CASE
  WHEN (`str_int` RLIKE '^[-+]?[0-9]*\\\\.?[0-9]+$')
  THEN CAST(`str_int` AS DOUBLE)
  ELSE NULL
END;
CASE
  WHEN (`str_float` RLIKE '^[-+]?[0-9]*\\\\.?[0-9]+$')
  THEN CAST(`str_float` AS DOUBLE)
  ELSE NULL
END;
CASE WHEN `bool_col` THEN 1 ELSE 0 END;
FLOOR(UNIX_TIMESTAMP(`date_col`) * 1000);
FLOOR(UNIX_TIMESTAMP(`timestamp_col`) * 1000);
`int_col`;
`float_col`;
CAST(`str_date` AS DATETIME(3));
CAST(`str_datetime` AS DATETIME(3));
FROM_UNIXTIME((
  `epoch_ms`
) / 1000);
FROM_UNIXTIME((
  CASE WHEN `bool_col` THEN 1 ELSE 0 END
) / 1000);
CAST(`date_col` AS DATETIME);
`timestamp_col`;
FLOOR(UNIX_TIMESTAMP(CAST(`str_date` AS DATETIME(3))) * 1000);
FROM_UNIXTIME((
  CASE WHEN `bool_col` THEN 1 ELSE 0 END
) / 1000);

-- === POSTGRES ===
CASE
  WHEN "str_int" ~ '^[-+]?[0-9]*\\.?[0-9]+$'
  THEN CAST("str_int" AS DOUBLE PRECISION)
  ELSE NULL
END;
CASE
  WHEN "str_float" ~ '^[-+]?[0-9]*\\.?[0-9]+$'
  THEN CAST("str_float" AS DOUBLE PRECISION)
  ELSE NULL
END;
CASE WHEN "bool_col" THEN 1 ELSE 0 END;
CAST(FLOOR(EXTRACT('epoch' FROM "date_col") * 1000) AS BIGINT);
CAST(FLOOR(EXTRACT('epoch' FROM "timestamp_col") * 1000) AS BIGINT);
"int_col";
"float_col";
CAST("str_date" AS TIMESTAMP);
CAST("str_datetime" AS TIMESTAMP);
TO_TIMESTAMP(CAST("epoch_ms" AS DOUBLE PRECISION) / 1000);
TO_TIMESTAMP(CAST(CASE WHEN "bool_col" THEN 1 ELSE 0 END AS DOUBLE PRECISION) / 1000);
CAST("date_col" AS TIMESTAMP);
"timestamp_col";
CAST(FLOOR(EXTRACT('epoch' FROM CAST("str_date" AS TIMESTAMP)) * 1000) AS BIGINT);
TO_TIMESTAMP(CAST(CASE WHEN "bool_col" THEN 1 ELSE 0 END AS DOUBLE PRECISION) / 1000);

-- === REDSHIFT ===
CASE
  WHEN "str_int" ~ '^[-+]?[0-9]*\\\\.?[0-9]+$'
  THEN CAST("str_int" AS DOUBLE PRECISION)
  ELSE NULL
END;
CASE
  WHEN "str_float" ~ '^[-+]?[0-9]*\\\\.?[0-9]+$'
  THEN CAST("str_float" AS DOUBLE PRECISION)
  ELSE NULL
END;
CASE WHEN "bool_col" THEN 1 ELSE 0 END;
CAST(EXTRACT('epoch' FROM "date_col") AS BIGINT) * 1000;
(
  (
    CAST(EXTRACT('millisecond' FROM "timestamp_col") AS BIGINT)
  ) + (
    CAST(EXTRACT('epoch' FROM "timestamp_col") AS BIGINT) * 1000
  )
);
"int_col";
"float_col";
CAST("str_date" AS TIMESTAMP);
CAST("str_datetime" AS TIMESTAMP);
(
  CAST('epoch' AS TIMESTAMP) + (
    (
      CAST((
        "epoch_ms"
      ) AS DOUBLE PRECISION) / 1000
    ) * INTERVAL '1 SECOND'
  )
);
(
  CAST('epoch' AS TIMESTAMP) + (
    (
      CAST((
        CASE WHEN "bool_col" THEN 1 ELSE 0 END
      ) AS DOUBLE PRECISION) / 1000
    ) * INTERVAL '1 SECOND'
  )
);
CAST("date_col" AS TIMESTAMP);
"timestamp_col";
(
  (
    CAST(EXTRACT('millisecond' FROM CAST("str_date" AS TIMESTAMP)) AS BIGINT)
  ) + (
    CAST(EXTRACT('epoch' FROM CAST("str_date" AS TIMESTAMP)) AS BIGINT) * 1000
  )
);
(
  CAST('epoch' AS TIMESTAMP) + (
    (
      CAST((
        CASE WHEN "bool_col" THEN 1 ELSE 0 END
      ) AS DOUBLE PRECISION) / 1000
    ) * INTERVAL '1 SECOND'
  )
);

-- === SNOWFLAKE ===
TRY_CAST("str_int" AS DOUBLE);
TRY_CAST("str_float" AS DOUBLE);
CASE WHEN "bool_col" THEN 1 ELSE 0 END;
DATE_PART('epoch_second', "date_col") * 1000;
DATE_PART('epoch_millisecond', "timestamp_col");
"int_col";
"float_col";
TRY_CAST("str_date" AS TIMESTAMP);
TRY_CAST("str_datetime" AS TIMESTAMP);
TO_TIMESTAMP_TZ("epoch_ms", 3);
TO_TIMESTAMP_TZ(CASE WHEN "bool_col" THEN 1 ELSE 0 END, 3);
CAST("date_col" AS TIMESTAMP);
"timestamp_col";
DATE_PART('epoch_millisecond', TRY_CAST("str_date" AS TIMESTAMP));
TO_TIMESTAMP_TZ(CASE WHEN "bool_col" THEN 1 ELSE 0 END, 3);

-- === SPARK ===
CAST(`str_int` AS DOUBLE);
CAST(`str_float` AS DOUBLE);
CASE WHEN `bool_col` THEN 1 ELSE 0 END;
(
  UNIX_TIMESTAMP(FROM_UTC_TIMESTAMP(CAST(`date_col` AS TIMESTAMP), CURRENT_TIMEZONE())) * 1000 + CAST(EXTRACT(seconds FROM `date_col`) % 1 * 1000 AS BIGINT)
);
(
  UNIX_TIMESTAMP(FROM_UTC_TIMESTAMP(CAST(`timestamp_col` AS TIMESTAMP), CURRENT_TIMEZONE())) * 1000 + CAST(EXTRACT(seconds FROM `timestamp_col`) % 1 * 1000 AS BIGINT)
);
`int_col`;
`float_col`;
CAST(`str_date` AS TIMESTAMP);
CAST(`str_datetime` AS TIMESTAMP);
DATE_ADD(
  MILLISECOND,
  (
    `epoch_ms`
  ) % 1000,
  TO_UTC_TIMESTAMP(CAST(FROM_UNIXTIME((
    `epoch_ms`
  ) / 1000) AS TIMESTAMP), CURRENT_TIMEZONE())
);
DATE_ADD(
  MILLISECOND,
  (
    CASE WHEN `bool_col` THEN 1 ELSE 0 END
  ) % 1000,
  TO_UTC_TIMESTAMP(
    CAST(FROM_UNIXTIME((
      CASE WHEN `bool_col` THEN 1 ELSE 0 END
    ) / 1000) AS TIMESTAMP),
    CURRENT_TIMEZONE()
  )
);
CAST(`date_col` AS TIMESTAMP);
`timestamp_col`;
(
  UNIX_TIMESTAMP(FROM_UTC_TIMESTAMP(CAST(`str_date` AS TIMESTAMP), CURRENT_TIMEZONE())) * 1000 + CAST(EXTRACT(seconds FROM CAST(`str_date` AS TIMESTAMP)) % 1 * 1000 AS BIGINT)
);
DATE_ADD(
  MILLISECOND,
  (
    CASE WHEN `bool_col` THEN 1 ELSE 0 END
  ) % 1000,
  TO_UTC_TIMESTAMP(
    CAST(FROM_UNIXTIME((
      CASE WHEN `bool_col` THEN 1 ELSE 0 END
    ) / 1000) AS TIMESTAMP),
    CURRENT_TIMEZONE()
  )
);

-- === TRINO ===
TRY_CAST("str_int" AS DOUBLE);
TRY_CAST("str_float" AS DOUBLE);
CASE WHEN "bool_col" THEN 1 ELSE 0 END;
CAST(FLOOR(TO_UNIXTIME("date_col") * 1000) AS BIGINT);
CAST(FLOOR(TO_UNIXTIME("timestamp_col") * 1000) AS BIGINT);
"int_col";
"float_col";
TRY_CAST("str_date" AS TIMESTAMP);
TRY_CAST("str_datetime" AS TIMESTAMP);
WITH_TIMEZONE(
  DATE_ADD(
    'MILLISECOND',
    (
      (
        "epoch_ms"
      ) % 1000
    ),
    CAST(FROM_UNIXTIME(FLOOR(CAST(CAST("epoch_ms" AS BIGINT) AS DOUBLE) / 1000)) AS TIMESTAMP)
  ),
  'UTC'
);
WITH_TIMEZONE(
  DATE_ADD(
    'MILLISECOND',
    (
      (
        CASE WHEN "bool_col" THEN 1 ELSE 0 END
      ) % 1000
    ),
    CAST(FROM_UNIXTIME(
      FLOOR(CAST(CAST(CASE WHEN "bool_col" THEN 1 ELSE 0 END AS BIGINT) AS DOUBLE) / 1000)
    ) AS TIMESTAMP)
  ),
  'UTC'
);
CAST("date_col" AS TIMESTAMP);
"timestamp_col";
CAST(FLOOR(TO_UNIXTIME(TRY_CAST("str_date" AS TIMESTAMP)) * 1000) AS BIGINT);
WITH_TIMEZONE(
  DATE_ADD(
    'MILLISECOND',
    (
      (
        CASE WHEN "bool_col" THEN 1 ELSE 0 END
      ) % 1000
    ),
    CAST(FROM_UNIXTIME(
      FLOOR(CAST(CAST(CASE WHEN "bool_col" THEN 1 ELSE 0 END AS BIGINT) AS DOUBLE) / 1000)
    ) AS TIMESTAMP)
  ),
  'UTC'
);
""")
