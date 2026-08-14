from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo
import polars as pl
import polars.testing as pl_testing
from hex_sl import Dataset
from hex_sl.dialect.base import HexSLDialect

from hex_sl_utils.datatype import DataType

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
        cls, expression_input_data: pl.DataFrame, dialect: HexSLDialect
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
        cls, expected_df: pl.DataFrame, result_df: pl.DataFrame, dialect: HexSLDialect
    ) -> None:
        assert result_df.shape == (4, 12)
        pl_testing.assert_frame_equal(
            result_df, expected_df, check_dtypes=False, atol=1e-6
        )

    @classmethod
    def get_result_dataset(cls, dialect: HexSLDialect, timezone: str) -> Dataset:
        return super().get_result_dataset(dialect, timezone="America/New_York")


# Database result tests

def test_snapshot_datetrunc_ts_tz_validate(dialect_name):
    """Test datetrunc timestamp with timezone expressions for each dialect separately."""
    dialect = HexSLDialect.from_name(dialect_name)
    result_df = SnapshotTest.get_result_df(dialect, timezone="America/New_York")
    expected_df = SnapshotTest.get_expected_df(dialect)
    SnapshotTest.validate(expected_df, result_df, dialect)
