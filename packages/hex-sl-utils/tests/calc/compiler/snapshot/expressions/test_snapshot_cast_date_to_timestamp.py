from __future__ import annotations

from datetime import date

import polars as pl
import pytest
from inline_snapshot import snapshot

from hex_sl_utils.datatype import DataType
from hex_sl_utils.dialect import Dialect

from ..snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    columns = {
        "date_col": DataType.DATE,
    }
    timezone = "America/New_York"

    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            # Date To Timestamp
            "todatetime(date_col)",
            # Date To Timestamp With Timezone
            "todatetime(date_col, 'America/New_York')",
        ]

    @classmethod
    def get_expression_input_data(cls) -> pl.DataFrame:
        df = pl.DataFrame(
            {
                "date_col": [
                    date(2021, 1, 1),
                    date(2021, 1, 2),
                    None,
                    date(2021, 1, 4),
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
                "col1": df["date_col"].cast(pl.Datetime),
                "col2": (df["date_col"].cast(pl.Datetime).dt.replace_time_zone(tz)),
            }
        )
        return expected_df


# Database result tests


def test_snapshot_cast_date_to_timestamp_validate(dialect_name):
    """Test cast date to timestamp expressions for each dialect separately."""
    dialect = Dialect.from_name(dialect_name)
    result_df = SnapshotTest.get_result_df(dialect, timezone="America/New_York")
    expected_df = SnapshotTest.get_expected_df(dialect)
    SnapshotTest.validate(expected_df, result_df, dialect)


@pytest.mark.database
@pytest.mark.database_local
def test_snapshot_cast_date_to_timestamp_result():
    """Test cast date to timestamp expressions for each dialect separately."""
    dialect_name = SnapshotTest.result_dialect
    dialect = Dialect.from_name(dialect_name)
    result_str = SnapshotTest.get_result_df_str(dialect, timezone="America/New_York")

    assert result_str == snapshot("""\
shape: (4, 3)
┌─────┬─────────────────────┬────────────────────────────────┐
│ row ┆ col1                ┆ col2                           │
│ --- ┆ ---                 ┆ ---                            │
│ i32 ┆ datetime[μs]        ┆ datetime[μs, America/New_York] │
╞═════╪═════════════════════╪════════════════════════════════╡
│ 0   ┆ 2021-01-01 00:00:00 ┆ 2021-01-01 00:00:00 EST        │
│ 1   ┆ 2021-01-02 00:00:00 ┆ 2021-01-02 00:00:00 EST        │
│ 2   ┆ null                ┆ null                           │
│ 3   ┆ 2021-01-04 00:00:00 ┆ 2021-01-04 00:00:00 EST        │
└─────┴─────────────────────┴────────────────────────────────┘\
""")
