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
