from __future__ import annotations

import polars as pl
import pytest
from inline_snapshot import snapshot

from hex_sl_utils.datatype import DataType
from hex_sl_utils.dialect import Dialect

from ..snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    columns = {
        "numeric_col": DataType.NUMBER,
        "bool_col": DataType.BOOLEAN,
    }

    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            "-numeric_col",
            "+numeric_col",
            "!bool_col",
            "!!bool_col",
        ]

    @classmethod
    def get_expression_input_data(cls) -> pl.DataFrame:
        df = pl.DataFrame(
            {
                "numeric_col": [-1, 1, -2, 2],
                "bool_col": [True, False, True, False],
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
                "col1": -df["numeric_col"],
                "col2": df["numeric_col"],
                "col3": ~df["bool_col"],
                "col4": ~(~df["bool_col"]),
            }
        )
        return expected_df


# Database result tests


def test_snapshot_unary_validate(dialect_name):
    """Test unary operator expressions for each dialect separately."""
    dialect = Dialect.from_name(dialect_name)
    result_df = SnapshotTest.get_result_df(dialect)
    expected_df = SnapshotTest.get_expected_df(dialect)
    SnapshotTest.validate(expected_df, result_df, dialect)


@pytest.mark.database
@pytest.mark.database_local
def test_snapshot_unary_result():
    """Test unary operator expressions for each dialect separately."""
    dialect_name = "duckdb"
    dialect = Dialect.from_name(dialect_name)
    result_str = SnapshotTest.get_result_df_str(dialect)

    assert result_str == snapshot("""\
shape: (4, 5)
┌─────┬──────┬──────┬───────┬───────┐
│ row ┆ col1 ┆ col2 ┆ col3  ┆ col4  │
│ --- ┆ ---  ┆ ---  ┆ ---   ┆ ---   │
│ i32 ┆ i32  ┆ i32  ┆ bool  ┆ bool  │
╞═════╪══════╪══════╪═══════╪═══════╡
│ 0   ┆ 1    ┆ -1   ┆ false ┆ true  │
│ 1   ┆ -1   ┆ 1    ┆ true  ┆ false │
│ 2   ┆ 2    ┆ -2   ┆ false ┆ true  │
│ 3   ┆ -2   ┆ 2    ┆ true  ┆ false │
└─────┴──────┴──────┴───────┴───────┘\
""")
