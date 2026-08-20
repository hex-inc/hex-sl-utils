from __future__ import annotations

import zoneinfo
from datetime import datetime

import polars as pl
import pytest
from inline_snapshot import snapshot

from hex_sl_utils.datatype import DataType
from hex_sl_utils.dialect import Dialect

from ..snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    columns = {
        "tstz_col": DataType.TIMESTAMPTZ,
    }
    timezone = "America/New_York"

    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            # TimestampTz To Date
            "toNumber(tstz_col < ToDatetime('2021-01-02 10:00:00'))",
            "toNumber(tstz_col < ToDate('2021-01-02'))",
        ]

    @classmethod
    def get_expression_input_data(cls) -> pl.DataFrame:
        utc = zoneinfo.ZoneInfo("UTC")
        df = pl.DataFrame(
            {
                "tstz_col": [
                    datetime(2021, 1, 2, 12, 15, 30, tzinfo=utc),  # 12:15:30 UTC
                    datetime(2021, 1, 2, 14, 45, 45, tzinfo=utc),  # 14:45:45 UTC
                    datetime(2021, 1, 2, 17, 30, 10, tzinfo=utc),  # 17:30:10 UTC
                ],
            }
        )
        return df

    @classmethod
    def get_expected_df_from_input(
        cls, expression_input_data: pl.DataFrame, dialect: Dialect
    ) -> pl.DataFrame:
        df = expression_input_data
        tz = "America/New_York"
        expected_df = pl.DataFrame(
            {
                "row": [0, 1, 2],
                "col1": pl.select(
                    (
                        df["tstz_col"]
                        .dt.convert_time_zone(tz)
                        .dt.replace_time_zone(None)
                        < pl.datetime(2021, 1, 2, 10, 0, 0)
                    ).cast(pl.Int32),
                ),
                "col2": pl.select(
                    (
                        df["tstz_col"]
                        .dt.convert_time_zone(tz)
                        .dt.replace_time_zone(None)
                        < pl.datetime(2021, 1, 2, 0, 0, 0)
                    ).cast(pl.Int32),
                ),
            }
        )
        return expected_df


# Database result tests


def test_snapshot_compare_timestamptz_to_timestamp_validate(dialect_name):
    """Test compare timestamptz to timestamp expressions for each dialect separately."""
    dialect = Dialect.from_name(dialect_name)
    result_df = SnapshotTest.get_result_df(dialect, timezone="America/New_York")
    expected_df = SnapshotTest.get_expected_df(dialect)
    SnapshotTest.validate(expected_df, result_df, dialect)


@pytest.mark.database
@pytest.mark.database_local
def test_snapshot_compare_timestamptz_to_timestamp_result():
    """Test compare timestamptz to timestamp expressions for each dialect separately."""
    dialect_name = SnapshotTest.result_dialect
    dialect = Dialect.from_name(dialect_name)
    result_str = SnapshotTest.get_result_df_str(dialect, timezone="America/New_York")

    assert result_str == snapshot("""\
shape: (3, 3)
┌─────┬──────┬──────┐
│ row ┆ col1 ┆ col2 │
│ --- ┆ ---  ┆ ---  │
│ i32 ┆ i32  ┆ i32  │
╞═════╪══════╪══════╡
│ 0   ┆ 1    ┆ 0    │
│ 1   ┆ 1    ┆ 0    │
│ 2   ┆ 0    ┆ 0    │
└─────┴──────┴──────┘\
""")
