from __future__ import annotations

from datetime import datetime
import polars as pl
from hex_sl.dialect.base import HexSLDialect

from hex_sl_utils.datatype import DataType

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
        cls, expression_input_data: pl.DataFrame, dialect: HexSLDialect
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
    dialect = HexSLDialect.from_name(dialect_name)
    result_df = SnapshotTest.get_result_df(dialect)
    expected_df = SnapshotTest.get_expected_df(dialect)
    SnapshotTest.validate(expected_df, result_df, dialect)
