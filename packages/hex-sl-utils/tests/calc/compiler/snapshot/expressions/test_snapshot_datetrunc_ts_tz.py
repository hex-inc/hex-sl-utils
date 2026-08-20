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
            "ts_tz",
            "truncyear(ts_tz)",
            "truncquarter(ts_tz)",
            "truncmonth(ts_tz)",
            "truncweek(ts_tz)",
            "truncweekmonday(ts_tz)",
            "truncday(ts_tz)",
            "trunchour(ts_tz)",
            "truncminute(ts_tz)",
            "truncsecond(ts_tz)",
            "truncmillisecond(ts_tz)",
        ]

    @classmethod
    def get_expression_input_data(cls) -> pl.DataFrame:
        df = pl.DataFrame(
            {
                "ts_tz": [
                    datetime(2021, 1, 1, 0, 0, 0, 123456, tzinfo=ZoneInfo("UTC")),
                    datetime(2022, 5, 15, 14, 45, 30, 456123, tzinfo=ZoneInfo("UTC")),
                    datetime(2023, 12, 30, 18, 20, 15, 789345, tzinfo=ZoneInfo("UTC")),
                    datetime(2024, 9, 12, 23, 59, 59, 987456, tzinfo=ZoneInfo("UTC")),
                ]
            }
        )
        return df

    @classmethod
    def get_expected_df_from_input(
        cls, expression_input_data: pl.DataFrame, dialect: Dialect
    ) -> pl.DataFrame:
        df = expression_input_data
        target_tz = "America/New_York"
        expected_df = pl.DataFrame(
            {
                "row": [0, 1, 2, 3],
                "col1": df.select(
                    pl.col("ts_tz").dt.convert_time_zone(target_tz)
                    if dialect.supports_microseconds_in_timestamps()
                    else pl.col("ts_tz")
                    .dt.convert_time_zone(target_tz)
                    .dt.truncate("1ms")
                ),
                "col2": df.select(
                    pl.col("ts_tz").dt.convert_time_zone(target_tz).dt.truncate("1y")
                ),
                "col3": df.select(
                    pl.col("ts_tz").dt.convert_time_zone(target_tz).dt.truncate("1q")
                ),
                "col4": df.select(
                    pl.col("ts_tz").dt.convert_time_zone(target_tz).dt.truncate("1mo")
                ),
                "col5": df.select(
                    pl.col("ts_tz").dt.convert_time_zone(target_tz).dt.truncate("1d")
                    - pl.duration(
                        days=(
                            pl.col("ts_tz").dt.convert_time_zone(target_tz).dt.weekday()
                            % 7
                            + 1
                        )
                    )
                    + pl.duration(days=1)
                ),
                "col6": df.select(
                    pl.col("ts_tz").dt.convert_time_zone(target_tz).dt.truncate("1w")
                ),
                "col7": df.select(
                    pl.col("ts_tz").dt.convert_time_zone(target_tz).dt.truncate("1d")
                ),
                "col8": df.select(
                    pl.col("ts_tz").dt.convert_time_zone(target_tz).dt.truncate("1h")
                ),
                "col9": df.select(
                    pl.col("ts_tz").dt.convert_time_zone(target_tz).dt.truncate("1m")
                ),
                "col10": df.select(
                    pl.col("ts_tz").dt.convert_time_zone(target_tz).dt.truncate("1s")
                ),
                "col11": df.select(
                    pl.col("ts_tz").dt.convert_time_zone(target_tz).dt.truncate("1ms")
                ),
            }
        )
        return expected_df

    @classmethod
    def validate(
        cls, expected_df: pl.DataFrame, result_df: pl.DataFrame, dialect: Dialect
    ) -> None:
        assert result_df.shape == (4, 12)
        pl_testing.assert_frame_equal(
            result_df, expected_df, check_dtypes=False, abs_tol=1e-6
        )


# Database result tests


def test_snapshot_datetrunc_ts_tz_validate(dialect_name):
    """Test datetrunc timestamp with timezone expressions for each dialect separately."""
    dialect = Dialect.from_name(dialect_name)
    result_df = SnapshotTest.get_result_df(dialect, timezone="America/New_York")
    expected_df = SnapshotTest.get_expected_df(dialect)
    SnapshotTest.validate(expected_df, result_df, dialect)


@pytest.mark.database
@pytest.mark.database_local
def test_snapshot_datetrunc_ts_tz_result():
    """Test datetrunc timestamp with timezone expressions for each dialect separately."""
    dialect_name = SnapshotTest.result_dialect
    dialect = Dialect.from_name(dialect_name)
    result_str = SnapshotTest.get_result_df_str(dialect, timezone="America/New_York")

    assert result_str == snapshot("""\
shape: (4, 12)
┌─────┬─────────────────┬─────────────────┬─────────────────┬─────────────────┬─────────────────┬─────────────────┬────────────────┬────────────────┬────────────────┬────────────────┬────────────────┐
│ row ┆ col1            ┆ col2            ┆ col3            ┆ col4            ┆ col5            ┆ col6            ┆ col7           ┆ col8           ┆ col9           ┆ col10          ┆ col11          │
│ --- ┆ ---             ┆ ---             ┆ ---             ┆ ---             ┆ ---             ┆ ---             ┆ ---            ┆ ---            ┆ ---            ┆ ---            ┆ ---            │
│ i32 ┆ datetime[μs,    ┆ datetime[μs,    ┆ datetime[μs,    ┆ datetime[μs,    ┆ datetime[μs,    ┆ datetime[μs,    ┆ datetime[μs,   ┆ datetime[μs,   ┆ datetime[μs,   ┆ datetime[μs,   ┆ datetime[μs,   │
│     ┆ America/New_Yor ┆ America/New_Yor ┆ America/New_Yor ┆ America/New_Yor ┆ America/New_Yor ┆ America/New_Yor ┆ America/New_Yo ┆ America/New_Yo ┆ America/New_Yo ┆ America/New_Yo ┆ America/New_Yo │
│     ┆ k]              ┆ k]              ┆ k]              ┆ k]              ┆ k]              ┆ k]              ┆ rk]            ┆ rk]            ┆ rk]            ┆ rk]            ┆ rk]            │
╞═════╪═════════════════╪═════════════════╪═════════════════╪═════════════════╪═════════════════╪═════════════════╪════════════════╪════════════════╪════════════════╪════════════════╪════════════════╡
│ 0   ┆ 2020-12-31      ┆ 2020-01-01      ┆ 2020-10-01      ┆ 2020-12-01      ┆ 2020-12-27      ┆ 2020-12-28      ┆ 2020-12-31     ┆ 2020-12-31     ┆ 2020-12-31     ┆ 2020-12-31     ┆ 2020-12-31     │
│     ┆ 19:00:00.123456 ┆ 00:00:00 EST    ┆ 00:00:00 EDT    ┆ 00:00:00 EST    ┆ 00:00:00 EST    ┆ 00:00:00 EST    ┆ 00:00:00 EST   ┆ 19:00:00 EST   ┆ 19:00:00 EST   ┆ 19:00:00 EST   ┆ 19:00:00.123   │
│     ┆ EST             ┆                 ┆                 ┆                 ┆                 ┆                 ┆                ┆                ┆                ┆                ┆ EST            │
│ 1   ┆ 2022-05-15      ┆ 2022-01-01      ┆ 2022-04-01      ┆ 2022-05-01      ┆ 2022-05-15      ┆ 2022-05-09      ┆ 2022-05-15     ┆ 2022-05-15     ┆ 2022-05-15     ┆ 2022-05-15     ┆ 2022-05-15     │
│     ┆ 10:45:30.456123 ┆ 00:00:00 EST    ┆ 00:00:00 EDT    ┆ 00:00:00 EDT    ┆ 00:00:00 EDT    ┆ 00:00:00 EDT    ┆ 00:00:00 EDT   ┆ 10:00:00 EDT   ┆ 10:45:00 EDT   ┆ 10:45:30 EDT   ┆ 10:45:30.456   │
│     ┆ EDT             ┆                 ┆                 ┆                 ┆                 ┆                 ┆                ┆                ┆                ┆                ┆ EDT            │
│ 2   ┆ 2023-12-30      ┆ 2023-01-01      ┆ 2023-10-01      ┆ 2023-12-01      ┆ 2023-12-24      ┆ 2023-12-25      ┆ 2023-12-30     ┆ 2023-12-30     ┆ 2023-12-30     ┆ 2023-12-30     ┆ 2023-12-30     │
│     ┆ 13:20:15.789345 ┆ 00:00:00 EST    ┆ 00:00:00 EDT    ┆ 00:00:00 EST    ┆ 00:00:00 EST    ┆ 00:00:00 EST    ┆ 00:00:00 EST   ┆ 13:00:00 EST   ┆ 13:20:00 EST   ┆ 13:20:15 EST   ┆ 13:20:15.789   │
│     ┆ EST             ┆                 ┆                 ┆                 ┆                 ┆                 ┆                ┆                ┆                ┆                ┆ EST            │
│ 3   ┆ 2024-09-12      ┆ 2024-01-01      ┆ 2024-07-01      ┆ 2024-09-01      ┆ 2024-09-08      ┆ 2024-09-09      ┆ 2024-09-12     ┆ 2024-09-12     ┆ 2024-09-12     ┆ 2024-09-12     ┆ 2024-09-12     │
│     ┆ 19:59:59.987456 ┆ 00:00:00 EST    ┆ 00:00:00 EDT    ┆ 00:00:00 EDT    ┆ 00:00:00 EDT    ┆ 00:00:00 EDT    ┆ 00:00:00 EDT   ┆ 19:00:00 EDT   ┆ 19:59:00 EDT   ┆ 19:59:59 EDT   ┆ 19:59:59.987   │
│     ┆ EDT             ┆                 ┆                 ┆                 ┆                 ┆                 ┆                ┆                ┆                ┆                ┆ EDT            │
└─────┴─────────────────┴─────────────────┴─────────────────┴─────────────────┴─────────────────┴─────────────────┴────────────────┴────────────────┴────────────────┴────────────────┴────────────────┘\
""")
