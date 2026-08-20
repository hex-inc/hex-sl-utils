from __future__ import annotations

import polars as pl
import polars.testing as pl_testing
import pytest
from inline_snapshot import snapshot

from hex_sl_utils.datatype import DataType
from hex_sl_utils.dialect import Dialect
from hex_sl_utils.dialect.clickhouse import ClickHouse

from ..snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    columns = {
        "ts_string_col": DataType.STRING,
    }

    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            "todatetime(ts_string_col)",
        ]

    @classmethod
    def get_expression_input_data(cls) -> pl.DataFrame:
        df = pl.DataFrame(
            {
                "ts_string_col": [
                    "2021-01-01 10:10:10",
                    "2021-01-02 11:11:11.123",
                    None,
                    "2021-01-04 13:13:13.321",
                ],
            }
        )
        return df

    @classmethod
    def get_expected_df_from_input(
        cls, expression_input_data: pl.DataFrame, dialect: Dialect
    ) -> pl.DataFrame:
        df = expression_input_data
        parse_formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S%.3f",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S%.3f",
        ]
        parsed_series = [
            df["ts_string_col"].str.strptime(pl.Datetime, fmt, strict=False)
            for fmt in parse_formats
        ]

        expected_df = pl.DataFrame(
            {
                "row": [0, 1, 2, 3],
                "col1": df.select(pl.coalesce(*parsed_series)),
            }
        )
        return expected_df

    @classmethod
    def validate(
        cls, expected_df: pl.DataFrame, result_df: pl.DataFrame, dialect: Dialect
    ) -> None:
        if isinstance(dialect, ClickHouse):
            # Remove timezone from ClickHouse datetime
            result_df = result_df.with_columns(
                col1=expected_df["col1"].dt.replace_time_zone(None),
            )

        pl_testing.assert_frame_equal(
            result_df,
            expected_df,
            check_dtypes=False,
            rel_tol=1e-3,
        )


# Database result tests


def test_snapshot_to_datetime_milliseconds_validate(dialect_name):
    """Test to_datetime milliseconds expressions for each dialect separately."""
    dialect = Dialect.from_name(dialect_name)
    result_df = SnapshotTest.get_result_df(dialect)
    expected_df = SnapshotTest.get_expected_df(dialect)
    SnapshotTest.validate(expected_df, result_df, dialect)


@pytest.mark.database
@pytest.mark.database_local
def test_snapshot_to_datetime_milliseconds_result():
    """Test to_datetime milliseconds expressions for each dialect separately."""
    dialect_name = "duckdb"
    dialect = Dialect.from_name(dialect_name)
    result_str = SnapshotTest.get_result_df_str(dialect)

    assert result_str == snapshot("""\
shape: (4, 2)
┌─────┬─────────────────────────┐
│ row ┆ col1                    │
│ --- ┆ ---                     │
│ i32 ┆ datetime[μs]            │
╞═════╪═════════════════════════╡
│ 0   ┆ 2021-01-01 10:10:10     │
│ 1   ┆ 2021-01-02 11:11:11.123 │
│ 2   ┆ null                    │
│ 3   ┆ 2021-01-04 13:13:13.321 │
└─────┴─────────────────────────┘\
""")
