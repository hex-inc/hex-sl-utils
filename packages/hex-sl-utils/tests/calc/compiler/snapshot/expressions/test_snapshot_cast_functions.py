from __future__ import annotations

from datetime import date, datetime

import polars as pl
import pytest
from inline_snapshot import snapshot

from hex_sl_utils.datatype import DataType
from hex_sl_utils.dialect import Dialect
from hex_sl_utils.dialect.clickhouse import ClickHouse
from hex_sl_utils.dialect.mssql import MSSQL

from ..snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    columns = {
        "int_col": DataType.NUMBER,
        "float_col": DataType.NUMBER,
        "bool_col": DataType.BOOLEAN,
        "date_col": DataType.DATE,
        "datetime_col": DataType.TIMESTAMP,
        "string_col": DataType.STRING,
        "ts_string_col": DataType.STRING,
        "date_string_col": DataType.STRING,
    }
    timezone = "America/New_York"

    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            # To string casts
            "totext(int_col)",
            "totext(float_col)",
            "totext(bool_col)",
            "totext(date_col)",
            "totext(datetime_col)",
            # To boolean casts
            "toboolean(int_col)",
            "toboolean(string_col)",
            # To numeric casts
            "tonumber(string_col)",
            "tonumber(bool_col)",
            # Date parsing
            "todate(date_string_col)",
            "todatetime(ts_string_col)",
            "todatetime(ts_string_col, 'UTC')",
            "todatetime(ts_string_col, 'America/New_York')",
        ]

    @classmethod
    def get_expression_input_data(cls) -> pl.DataFrame:
        return pl.DataFrame(
            {
                "int_col": [-1, 10, 0, 2],
                "float_col": [2.5, 2.0, -12.0, 2.001],
                "bool_col": [True, False, True, False],
                "date_col": [
                    date(2021, 1, 1),
                    date(2021, 1, 2),
                    date(2021, 1, 3),
                    date(2021, 1, 4),
                ],
                "datetime_col": [
                    datetime(2021, 1, 1, 10, 10, 10),
                    datetime(2021, 1, 2, 11, 11, 11),
                    datetime(2021, 1, 3, 12, 12, 12),
                    datetime(2021, 1, 4, 13, 13, 13),
                ],
                "string_col": ["0", "FALSE", "1.50", "TRUE"],
                "ts_string_col": [
                    "2021-01-01 10:10:10",
                    "2021-01-02 11:11:11",
                    None,
                    "2021-01-04 13:13:13",
                ],
                "date_string_col": ["2021-01-01", "bogus", "2021-01-03", "2021-01-04"],
            }
        )

    @classmethod
    def get_expected_df_from_input(
        cls, expression_input_data: pl.DataFrame, dialect: Dialect
    ) -> pl.DataFrame:
        df = expression_input_data
        expected_df = pl.DataFrame(
            {
                "row": [0, 1, 2, 3],
                "col1": df["int_col"].cast(pl.Utf8),
                "col2": df["float_col"].cast(pl.Utf8),
                "col3": df.select(
                    pl.when(pl.col("bool_col"))
                    .then(pl.lit("true"))
                    .otherwise(pl.lit("false"))
                    .alias("col3")
                )["col3"],
                "col4": df["date_col"].cast(pl.Utf8),
                "col5": df["datetime_col"].dt.strftime("%Y-%m-%d %H:%M:%S"),
                "col6": df["int_col"] != 0,
                "col7": df.select(
                    pl.when(
                        pl.col("string_col").str.to_lowercase().is_in(["true", "1"])
                    )
                    .then(True)
                    .when(pl.col("string_col").str.to_lowercase().is_in(["false", "0"]))
                    .then(False)
                    .otherwise(
                        # MSSQL doesn't support null booleans
                        False if isinstance(dialect, MSSQL) else None
                    )
                    .alias("col7")
                )["col7"],
                "col8": df["string_col"].cast(pl.Float64, strict=False),
                "col9": df["bool_col"].cast(pl.Int32),
                "col10": df["date_string_col"].str.strptime(
                    pl.Date, "%Y-%m-%d", strict=False
                ),
                "col11": df["ts_string_col"].str.strptime(
                    pl.Datetime, "%Y-%m-%d %H:%M:%S", strict=False
                ),
                "col12": (
                    df["ts_string_col"]
                    .str.strptime(pl.Datetime, "%Y-%m-%d %H:%M:%S", strict=False)
                    .dt.replace_time_zone("UTC")
                    .dt.convert_time_zone("America/New_York")
                ),
                "col13": (
                    df["ts_string_col"]
                    .str.strptime(pl.Datetime, "%Y-%m-%d %H:%M:%S", strict=False)
                    .dt.replace_time_zone("America/New_York")
                ),
            }
        )
        return expected_df

    @classmethod
    def validate(
        cls, expected_df: pl.DataFrame, result_df: pl.DataFrame, dialect: Dialect
    ) -> None:
        # Convert col2 (float to string) to handle formatting differences
        expected_col2 = expected_df["col2"].to_list()
        result_col2 = result_df["col2"].to_list()

        # Normalize float formatting (remove trailing zeros after decimal)
        for i in range(len(expected_col2)):
            if expected_col2[i] is not None:
                # Normalize by converting to float and back to string
                expected_col2[i] = str(float(expected_col2[i]))
            if result_col2[i] is not None:
                result_col2[i] = str(float(result_col2[i]))

        # Create modified dataframes for comparison
        expected_df_mod = expected_df.with_columns(pl.Series("col2", expected_col2))
        result_df_mod = result_df.with_columns(pl.Series("col2", result_col2))

        # Handle timezone differences for columns 11 and 12
        if isinstance(dialect, ClickHouse):
            # Remove timezone from dialects that always parse timestamp strings into
            #  timezone aware timestamps
            result_df_mod = result_df_mod.with_columns(
                col11=expected_df["col11"].dt.replace_time_zone(None)
            )

        super().validate(expected_df_mod, result_df_mod, dialect)


# Database result tests


def test_snapshot_cast_functions_validate(dialect_name):
    """Test cast functions validation for each dialect."""
    dialect = Dialect.from_name(dialect_name)
    result_df = SnapshotTest.get_result_df(dialect, timezone="America/New_York")
    expected_df = SnapshotTest.get_expected_df(dialect)
    SnapshotTest.validate(expected_df, result_df, dialect)


@pytest.mark.database
@pytest.mark.database_local
def test_snapshot_cast_functions_result():
    """Test cast functions result output."""
    dialect = Dialect.from_name("duckdb")
    result_str = SnapshotTest.get_result_df_str(dialect, timezone="America/New_York")

    assert result_str == snapshot("""\
shape: (4, 14)
┌─────┬──────┬───────┬───────┬────────────┬─────────────────────┬───────┬───────┬──────┬──────┬────────────┬─────────────────────┬────────────────────────────────┬────────────────────────────────┐
│ row ┆ col1 ┆ col2  ┆ col3  ┆ col4       ┆ col5                ┆ col6  ┆ col7  ┆ col8 ┆ col9 ┆ col10      ┆ col11               ┆ col12                          ┆ col13                          │
│ --- ┆ ---  ┆ ---   ┆ ---   ┆ ---        ┆ ---                 ┆ ---   ┆ ---   ┆ ---  ┆ ---  ┆ ---        ┆ ---                 ┆ ---                            ┆ ---                            │
│ i32 ┆ str  ┆ str   ┆ str   ┆ str        ┆ str                 ┆ bool  ┆ bool  ┆ f64  ┆ i32  ┆ date       ┆ datetime[μs]        ┆ datetime[μs, America/New_York] ┆ datetime[μs, America/New_York] │
╞═════╪══════╪═══════╪═══════╪════════════╪═════════════════════╪═══════╪═══════╪══════╪══════╪════════════╪═════════════════════╪════════════════════════════════╪════════════════════════════════╡
│ 0   ┆ -1   ┆ 2.500 ┆ true  ┆ 2021-01-01 ┆ 2021-01-01 10:10:10 ┆ true  ┆ false ┆ 0.0  ┆ 1    ┆ 2021-01-01 ┆ 2021-01-01 10:10:10 ┆ 2021-01-01 05:10:10 EST        ┆ 2021-01-01 10:10:10 EST        │
│ 1   ┆ 10   ┆ 2     ┆ false ┆ 2021-01-02 ┆ 2021-01-02 11:11:11 ┆ true  ┆ false ┆ null ┆ 0    ┆ null       ┆ 2021-01-02 11:11:11 ┆ 2021-01-02 06:11:11 EST        ┆ 2021-01-02 11:11:11 EST        │
│ 2   ┆ 0    ┆ -12   ┆ true  ┆ 2021-01-03 ┆ 2021-01-03 12:12:12 ┆ false ┆ null  ┆ 1.5  ┆ 1    ┆ 2021-01-03 ┆ null                ┆ null                           ┆ null                           │
│ 3   ┆ 2    ┆ 2.001 ┆ false ┆ 2021-01-04 ┆ 2021-01-04 13:13:13 ┆ true  ┆ true  ┆ null ┆ 0    ┆ 2021-01-04 ┆ 2021-01-04 13:13:13 ┆ 2021-01-04 08:13:13 EST        ┆ 2021-01-04 13:13:13 EST        │
└─────┴──────┴───────┴───────┴────────────┴─────────────────────┴───────┴───────┴──────┴──────┴────────────┴─────────────────────┴────────────────────────────────┴────────────────────────────────┘\
""")
