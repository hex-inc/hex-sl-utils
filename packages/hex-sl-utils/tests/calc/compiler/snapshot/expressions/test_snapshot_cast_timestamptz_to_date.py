from __future__ import annotations

import zoneinfo
from datetime import datetime

import polars as pl

from hex_sl_utils.datatype import DataType
from hex_sl_utils.dialect import Dialect

from ..snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    columns = {
        "tstz_col": DataType.TIMESTAMPTZ,
        "ts_col": DataType.TIMESTAMP,
    }
    timezone = "America/New_York"

    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            # TimestampTz To Date
            "todate(tstz_col)",
            # Timestamp To Date
            "todate(ts_col)",
        ]

    @classmethod
    def get_expression_input_data(cls) -> pl.DataFrame:
        utc = zoneinfo.ZoneInfo("UTC")
        df = pl.DataFrame(
            {
                "tstz_col": [
                    datetime(2021, 1, 1, 0, 10, 10, tzinfo=utc),
                    datetime(2021, 1, 2, 11, 11, 11, tzinfo=utc),
                    None,
                    datetime(2021, 1, 4, 13, 13, 13, tzinfo=utc),
                ],
                "ts_col": [
                    datetime(2021, 1, 1, 0, 10, 10),
                    datetime(2021, 1, 2, 11, 11, 11),
                    None,
                    datetime(2021, 1, 4, 13, 13, 13),
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
                "row": [0, 1, 2, 3],
                "col1": (
                    df["tstz_col"]
                    .dt.convert_time_zone(tz)
                    .dt.replace_time_zone(None)
                    .cast(pl.Date)
                ),
                "col2": df["ts_col"].cast(pl.Date),
            }
        )
        return expected_df


# Database result tests


def test_snapshot_cast_timestamptz_to_date_validate(dialect_name):
    """Test cast timestamptz to date expressions for each dialect separately."""
    dialect = Dialect.from_name(dialect_name)
    result_df = SnapshotTest.get_result_df(dialect, timezone="America/New_York")
    expected_df = SnapshotTest.get_expected_df(dialect)
    SnapshotTest.validate(expected_df, result_df, dialect)
