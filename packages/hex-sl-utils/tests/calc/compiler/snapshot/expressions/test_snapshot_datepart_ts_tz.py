from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import polars as pl
import polars.testing as pl_testing

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
