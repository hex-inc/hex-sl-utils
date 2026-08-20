from __future__ import annotations

import polars as pl
import pytest
from inline_snapshot import snapshot

from hex_sl_utils.datatype import DataType
from hex_sl_utils.dialect import Dialect

from ..snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    columns = {
        "lhs": DataType.NUMBER,
        "rhs": DataType.NUMBER,
    }

    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            "lhs < rhs",
            "lhs <= rhs",
            "lhs <= rhs",
            "lhs > rhs",
            "lhs >= rhs",
            "lhs >= rhs",
            "lhs == rhs",
            "lhs != rhs",
            "lhs != rhs",
        ]

    @classmethod
    def get_expression_input_data(cls) -> pl.DataFrame:
        return pl.DataFrame(
            {
                "lhs": [-1, 10, -2, 2],
                "rhs": [2, 10, -12, 2],
            }
        )

    @classmethod
    def get_expected_df_from_input(
        cls, expression_input_data: pl.DataFrame, dialect: Dialect
    ) -> pl.DataFrame:
        df = expression_input_data
        expected_df = pl.DataFrame(
            {
                "row": [0, 1, 2, 3],
                "col1": df["lhs"] < df["rhs"],
                "col2": df["lhs"] <= df["rhs"],
                "col3": df["lhs"] <= df["rhs"],
                "col4": df["lhs"] > df["rhs"],
                "col5": df["lhs"] >= df["rhs"],
                "col6": df["lhs"] >= df["rhs"],
                "col7": df["lhs"] == df["rhs"],
                "col8": df["lhs"] != df["rhs"],
                "col9": df["lhs"] != df["rhs"],
            }
        )
        return expected_df


# Database result tests


def test_snapshot_binary_comparison_validate(dialect_name):
    """Test binary comparison validation for each dialect."""
    dialect = Dialect.from_name(dialect_name)
    result_df = SnapshotTest.get_result_df(dialect)
    expected_df = SnapshotTest.get_expected_df(dialect)
    SnapshotTest.validate(expected_df, result_df, dialect)


@pytest.mark.database
@pytest.mark.database_local
def test_snapshot_binary_comparison_result():
    """Test binary comparison result output."""
    dialect = Dialect.from_name("duckdb")
    result_str = SnapshotTest.get_result_df_str(dialect)

    assert result_str == snapshot("""\
shape: (4, 10)
┌─────┬───────┬───────┬───────┬───────┬───────┬───────┬───────┬───────┬───────┐
│ row ┆ col1  ┆ col2  ┆ col3  ┆ col4  ┆ col5  ┆ col6  ┆ col7  ┆ col8  ┆ col9  │
│ --- ┆ ---   ┆ ---   ┆ ---   ┆ ---   ┆ ---   ┆ ---   ┆ ---   ┆ ---   ┆ ---   │
│ i32 ┆ bool  ┆ bool  ┆ bool  ┆ bool  ┆ bool  ┆ bool  ┆ bool  ┆ bool  ┆ bool  │
╞═════╪═══════╪═══════╪═══════╪═══════╪═══════╪═══════╪═══════╪═══════╪═══════╡
│ 0   ┆ true  ┆ true  ┆ true  ┆ false ┆ false ┆ false ┆ false ┆ true  ┆ true  │
│ 1   ┆ false ┆ true  ┆ true  ┆ false ┆ true  ┆ true  ┆ true  ┆ false ┆ false │
│ 2   ┆ false ┆ false ┆ false ┆ true  ┆ true  ┆ true  ┆ false ┆ true  ┆ true  │
│ 3   ┆ false ┆ true  ┆ true  ┆ false ┆ true  ┆ true  ┆ true  ┆ false ┆ false │
└─────┴───────┴───────┴───────┴───────┴───────┴───────┴───────┴───────┴───────┘\
""")
