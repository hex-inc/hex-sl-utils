from __future__ import annotations

import polars as pl
import pytest
from inline_snapshot import snapshot

from hex_sl_utils.datatype import DataType
from hex_sl_utils.dialect import Dialect

from ..snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    columns = {
        "bool_col1": DataType.BOOLEAN,
        "bool_col2": DataType.BOOLEAN,
        "int_col": DataType.NUMBER,
    }

    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            # AND operations
            "bool_col1 AND bool_col2",
            "bool_col1 AND TRUE",
            "bool_col1 AND FALSE",
            # OR operations
            "bool_col1 OR bool_col2",
            "bool_col1 OR TRUE",
            "bool_col1 OR FALSE",
            # Mixed operations
            "(bool_col1 AND bool_col2) OR NOT bool_col1",
            "bool_col1 AND (int_col > 0)",
            "(bool_col1 AND bool_col2) == (bool_col1 OR bool_col2)",
        ]

    @classmethod
    def get_expression_input_data(cls) -> pl.DataFrame:
        return pl.DataFrame(
            {
                "bool_col1": [True, False, True, False],
                "bool_col2": [False, True, True, False],
                "int_col": [1, 0, 1, 0],
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
                "col1": df["bool_col1"] & df["bool_col2"],
                "col2": df["bool_col1"] & True,
                "col3": df["bool_col1"] & False,
                "col4": df["bool_col1"] | df["bool_col2"],
                "col5": df["bool_col1"] | True,
                "col6": df["bool_col1"] | False,
                "col7": (df["bool_col1"] & df["bool_col2"]) | ~df["bool_col1"],
                "col8": df["bool_col1"] & (df["int_col"] > 0),
                "col9": (df["bool_col1"] & df["bool_col2"])
                == (df["bool_col1"] | df["bool_col2"]),
            }
        )
        return expected_df


# Database result tests


def test_snapshot_binary_logical_validate(dialect_name):
    """Test binary logical validation for each dialect."""
    dialect = Dialect.from_name(dialect_name)
    result_df = SnapshotTest.get_result_df(dialect)
    expected_df = SnapshotTest.get_expected_df(dialect)
    SnapshotTest.validate(expected_df, result_df, dialect)


@pytest.mark.database
@pytest.mark.database_local
def test_snapshot_binary_logical_result():
    """Test binary logical result output."""
    dialect = Dialect.from_name("duckdb")
    result_str = SnapshotTest.get_result_df_str(dialect)

    assert result_str == snapshot("""\
shape: (4, 10)
┌─────┬───────┬───────┬───────┬───────┬──────┬───────┬───────┬───────┬───────┐
│ row ┆ col1  ┆ col2  ┆ col3  ┆ col4  ┆ col5 ┆ col6  ┆ col7  ┆ col8  ┆ col9  │
│ --- ┆ ---   ┆ ---   ┆ ---   ┆ ---   ┆ ---  ┆ ---   ┆ ---   ┆ ---   ┆ ---   │
│ i32 ┆ bool  ┆ bool  ┆ bool  ┆ bool  ┆ bool ┆ bool  ┆ bool  ┆ bool  ┆ bool  │
╞═════╪═══════╪═══════╪═══════╪═══════╪══════╪═══════╪═══════╪═══════╪═══════╡
│ 0   ┆ false ┆ true  ┆ false ┆ true  ┆ true ┆ true  ┆ false ┆ true  ┆ false │
│ 1   ┆ false ┆ false ┆ false ┆ true  ┆ true ┆ false ┆ true  ┆ false ┆ false │
│ 2   ┆ true  ┆ true  ┆ false ┆ true  ┆ true ┆ true  ┆ true  ┆ true  ┆ true  │
│ 3   ┆ false ┆ false ┆ false ┆ false ┆ true ┆ false ┆ true  ┆ false ┆ true  │
└─────┴───────┴───────┴───────┴───────┴──────┴───────┴───────┴───────┴───────┘\
""")
