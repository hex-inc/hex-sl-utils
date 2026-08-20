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
        "d": DataType.DATE,
    }

    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            "year(d)",
            "quarter(d)",
            "month(d)",
            "day(d)",
            "dayofweek(d)",
            "hour(d)",
            "minute(d)",
            "second(d)",
            "millisecond(d)",
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
                "col1": df.select(pl.col("d").dt.year()),
                "col2": df.select(pl.col("d").dt.quarter()),
                "col3": df.select(pl.col("d").dt.month()),
                "col4": df.select(pl.col("d").dt.day()),
                "col5": df.select(pl.col("d").dt.weekday() % 7 + 1),
                "col6": [0] * 4,
                "col7": [0] * 4,
                "col8": [0] * 4,
                "col9": [0] * 4,
            }
        )
        return expected_df


# Database result tests


def test_snapshot_datepart_date_validate(dialect_name):
    """Test datepart date expressions for each dialect separately."""
    dialect = Dialect.from_name(dialect_name)
    result_df = SnapshotTest.get_result_df(dialect)
    expected_df = SnapshotTest.get_expected_df(dialect)
    SnapshotTest.validate(expected_df, result_df, dialect)


@pytest.mark.database
@pytest.mark.database_local
def test_snapshot_datepart_date_result():
    """Test datepart date expressions for each dialect separately."""
    dialect_name = SnapshotTest.result_dialect
    dialect = Dialect.from_name(dialect_name)
    result_str = SnapshotTest.get_result_df_str(dialect)

    assert result_str == snapshot("""\
shape: (4, 10)
┌─────┬──────┬──────┬──────┬──────┬──────┬──────┬──────┬──────┬──────┐
│ row ┆ col1 ┆ col2 ┆ col3 ┆ col4 ┆ col5 ┆ col6 ┆ col7 ┆ col8 ┆ col9 │
│ --- ┆ ---  ┆ ---  ┆ ---  ┆ ---  ┆ ---  ┆ ---  ┆ ---  ┆ ---  ┆ ---  │
│ i32 ┆ i64  ┆ i64  ┆ i64  ┆ i64  ┆ i64  ┆ i32  ┆ i32  ┆ i32  ┆ i32  │
╞═════╪══════╪══════╪══════╪══════╪══════╪══════╪══════╪══════╪══════╡
│ 0   ┆ 2021 ┆ 1    ┆ 1    ┆ 1    ┆ 6    ┆ 0    ┆ 0    ┆ 0    ┆ 0    │
│ 1   ┆ 2022 ┆ 2    ┆ 5    ┆ 15   ┆ 1    ┆ 0    ┆ 0    ┆ 0    ┆ 0    │
│ 2   ┆ 2023 ┆ 4    ┆ 12   ┆ 30   ┆ 7    ┆ 0    ┆ 0    ┆ 0    ┆ 0    │
│ 3   ┆ 2024 ┆ 3    ┆ 9    ┆ 12   ┆ 5    ┆ 0    ┆ 0    ┆ 0    ┆ 0    │
└─────┴──────┴──────┴──────┴──────┴──────┴──────┴──────┴──────┴──────┘\
""")
