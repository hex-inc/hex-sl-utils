from __future__ import annotations

from datetime import date

import polars as pl
import polars.testing as pl_testing
import pytest
from inline_snapshot import snapshot

from hex_sl_utils.datatype import DataType
from hex_sl_utils.dialect import Dialect

from ..snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    columns = {
        "d": DataType.DATE,
    }
    timezone = "America/New_York"

    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            "d",
            "truncyear(d)",
            "truncquarter(d)",
            "truncmonth(d)",
            "truncweek(d)",
            "truncweekmonday(d)",
            "truncday(d)",
            "trunchour(d)",
            "truncminute(d)",
            "truncsecond(d)",
            "truncmillisecond(d)",
        ]

    @classmethod
    def get_expression_input_data(cls) -> pl.DataFrame:
        df = pl.DataFrame(
            {
                "d": [
                    date(2021, 1, 1),
                    date(2022, 5, 15),
                    date(2023, 12, 30),
                    date(2024, 9, 12),
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
                "col1": df["d"],
                "col2": df.select(pl.col("d").dt.truncate("1y")),
                "col3": df.select(pl.col("d").dt.truncate("1q")),
                "col4": df.select(pl.col("d").dt.truncate("1mo")),
                "col5": df.select(
                    # Truncate to Sunday-based week
                    pl.col("d")
                    - pl.duration(days=pl.col("d").dt.weekday() % 7 + 1)
                    + pl.duration(days=1)
                ),
                "col6": df.select(pl.col("d").dt.truncate("1w")),
                "col7": df.select(pl.col("d").dt.truncate("1d")),
                "col8": df["d"],
                "col9": df["d"],
                "col10": df["d"],
                "col11": df["d"],
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


def test_snapshot_datetrunc_date_validate(dialect_name):
    """Test datetrunc date expressions for each dialect separately."""
    dialect = Dialect.from_name(dialect_name)
    result_df = SnapshotTest.get_result_df(dialect)
    expected_df = SnapshotTest.get_expected_df(dialect)
    SnapshotTest.validate(expected_df, result_df, dialect)


@pytest.mark.database
@pytest.mark.database_local
def test_snapshot_datetrunc_date_result():
    """Test datetrunc date expressions for each dialect separately."""
    dialect_name = "duckdb"
    dialect = Dialect.from_name(dialect_name)
    result_str = SnapshotTest.get_result_df_str(dialect)

    assert result_str == snapshot("""\
shape: (4, 12)
┌─────┬────────────┬────────────┬────────────┬────────────┬────────────┬────────────┬────────────┬────────────┬────────────┬────────────┬────────────┐
│ row ┆ col1       ┆ col2       ┆ col3       ┆ col4       ┆ col5       ┆ col6       ┆ col7       ┆ col8       ┆ col9       ┆ col10      ┆ col11      │
│ --- ┆ ---        ┆ ---        ┆ ---        ┆ ---        ┆ ---        ┆ ---        ┆ ---        ┆ ---        ┆ ---        ┆ ---        ┆ ---        │
│ i32 ┆ date       ┆ date       ┆ date       ┆ date       ┆ date       ┆ date       ┆ date       ┆ date       ┆ date       ┆ date       ┆ date       │
╞═════╪════════════╪════════════╪════════════╪════════════╪════════════╪════════════╪════════════╪════════════╪════════════╪════════════╪════════════╡
│ 0   ┆ 2021-01-01 ┆ 2021-01-01 ┆ 2021-01-01 ┆ 2021-01-01 ┆ 2020-12-27 ┆ 2020-12-28 ┆ 2021-01-01 ┆ 2021-01-01 ┆ 2021-01-01 ┆ 2021-01-01 ┆ 2021-01-01 │
│ 1   ┆ 2022-05-15 ┆ 2022-01-01 ┆ 2022-04-01 ┆ 2022-05-01 ┆ 2022-05-15 ┆ 2022-05-09 ┆ 2022-05-15 ┆ 2022-05-15 ┆ 2022-05-15 ┆ 2022-05-15 ┆ 2022-05-15 │
│ 2   ┆ 2023-12-30 ┆ 2023-01-01 ┆ 2023-10-01 ┆ 2023-12-01 ┆ 2023-12-24 ┆ 2023-12-25 ┆ 2023-12-30 ┆ 2023-12-30 ┆ 2023-12-30 ┆ 2023-12-30 ┆ 2023-12-30 │
│ 3   ┆ 2024-09-12 ┆ 2024-01-01 ┆ 2024-07-01 ┆ 2024-09-01 ┆ 2024-09-08 ┆ 2024-09-09 ┆ 2024-09-12 ┆ 2024-09-12 ┆ 2024-09-12 ┆ 2024-09-12 ┆ 2024-09-12 │
└─────┴────────────┴────────────┴────────────┴────────────┴────────────┴────────────┴────────────┴────────────┴────────────┴────────────┴────────────┘\
""")
