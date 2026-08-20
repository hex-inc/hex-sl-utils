from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import polars as pl
import pytest
from inline_snapshot import snapshot

from hex_sl_utils.datatype import DataType
from hex_sl_utils.dialect import Dialect

from ..snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    columns = {
        "ts": DataType.TIMESTAMP,
        "d": DataType.DATE,
        "ts_tz": DataType.TIMESTAMPTZ,
    }
    timezone = "America/New_York"

    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            "datetimetoepochms(d)",
            "datetimetoepochms(ts)",
            "datetimetoepochms(ts_tz)",
            "epochmstodatetime(datetimetoepochms(d))",
            "epochmstodatetime(datetimetoepochms(ts))",
            "epochmstodatetime(datetimetoepochms(ts_tz))",
        ]

    @classmethod
    def get_expression_input_data(cls) -> pl.DataFrame:
        ts = [
            datetime(2021, 1, 1, 0, 0, 0, 123000),
            datetime(2022, 5, 15, 14, 45, 30, 456000),
            datetime(2023, 12, 30, 18, 20, 15, 789000),
            datetime(2024, 9, 12, 23, 59, 59, 999000),
        ]

        df = pl.DataFrame(
            {
                "ts": ts,
                "d": [t.date() for t in ts],
                "ts_tz": [t.replace(tzinfo=ZoneInfo("UTC")) for t in ts],
            }
        )
        return df

    @classmethod
    def get_expected_df_from_input(
        cls, expression_input_data: pl.DataFrame, dialect: Dialect
    ) -> pl.DataFrame:
        df = expression_input_data
        timezone = "America/New_York"
        expected_df = pl.DataFrame(
            {
                "row": [0, 1, 2, 3],
                "col1": df.select(pl.col("d").dt.timestamp("ms")),
                "col2": df.select(pl.col("ts").dt.timestamp("ms")),
                "col3": df.select(pl.col("ts_tz").dt.timestamp("ms")),
                "col4": df.select(
                    pl.from_epoch(pl.col("d").dt.timestamp("ms"), time_unit="ms")
                    .dt.replace_time_zone("UTC")
                    .dt.convert_time_zone(timezone),
                ),
                "col5": df.select(
                    pl.from_epoch(pl.col("ts").dt.timestamp("ms"), time_unit="ms")
                    .dt.replace_time_zone("UTC")
                    .dt.convert_time_zone(timezone)
                ),
                "col6": df.select(
                    pl.from_epoch(pl.col("ts_tz").dt.timestamp("ms"), time_unit="ms")
                    .dt.replace_time_zone("UTC")
                    .dt.convert_time_zone(timezone)
                ),
            }
        )
        return expected_df


# Database result tests


def test_snapshot_datepart_epochms_validate(dialect_name):
    """Test datepart epochms expressions for each dialect separately."""
    dialect = Dialect.from_name(dialect_name)
    result_df = SnapshotTest.get_result_df(dialect, timezone="America/New_York")
    expected_df = SnapshotTest.get_expected_df(dialect)
    SnapshotTest.validate(expected_df, result_df, dialect)


@pytest.mark.database
@pytest.mark.database_local
def test_snapshot_datepart_epochms_result():
    """Test datepart epochms expressions for each dialect separately."""
    dialect_name = SnapshotTest.result_dialect
    dialect = Dialect.from_name(dialect_name)
    result_str = SnapshotTest.get_result_df_str(dialect, timezone="America/New_York")

    assert result_str == snapshot("""\
shape: (4, 7)
┌─────┬───────────────┬───────────────┬───────────────┬────────────────────────────────┬────────────────────────────────┬────────────────────────────────┐
│ row ┆ col1          ┆ col2          ┆ col3          ┆ col4                           ┆ col5                           ┆ col6                           │
│ --- ┆ ---           ┆ ---           ┆ ---           ┆ ---                            ┆ ---                            ┆ ---                            │
│ i32 ┆ i64           ┆ i64           ┆ i64           ┆ datetime[μs, America/New_York] ┆ datetime[μs, America/New_York] ┆ datetime[μs, America/New_York] │
╞═════╪═══════════════╪═══════════════╪═══════════════╪════════════════════════════════╪════════════════════════════════╪════════════════════════════════╡
│ 0   ┆ 1609459200000 ┆ 1609459200123 ┆ 1609459200123 ┆ 2020-12-31 19:00:00 EST        ┆ 2020-12-31 19:00:00.123 EST    ┆ 2020-12-31 19:00:00.123 EST    │
│ 1   ┆ 1652572800000 ┆ 1652625930456 ┆ 1652625930456 ┆ 2022-05-14 20:00:00 EDT        ┆ 2022-05-15 10:45:30.456 EDT    ┆ 2022-05-15 10:45:30.456 EDT    │
│ 2   ┆ 1703894400000 ┆ 1703960415789 ┆ 1703960415789 ┆ 2023-12-29 19:00:00 EST        ┆ 2023-12-30 13:20:15.789 EST    ┆ 2023-12-30 13:20:15.789 EST    │
│ 3   ┆ 1726099200000 ┆ 1726185599999 ┆ 1726185599999 ┆ 2024-09-11 20:00:00 EDT        ┆ 2024-09-12 19:59:59.999 EDT    ┆ 2024-09-12 19:59:59.999 EDT    │
└─────┴───────────────┴───────────────┴───────────────┴────────────────────────────────┴────────────────────────────────┴────────────────────────────────┘\
""")
