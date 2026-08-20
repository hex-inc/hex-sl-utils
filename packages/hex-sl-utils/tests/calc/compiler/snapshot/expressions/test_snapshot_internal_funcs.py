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
