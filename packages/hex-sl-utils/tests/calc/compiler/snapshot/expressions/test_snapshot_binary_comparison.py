from __future__ import annotations

import polars as pl
from hex_sl.dialect.base import HexSLDialect

from hex_sl_utils.datatype import DataType

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
        cls, expression_input_data: pl.DataFrame, dialect: HexSLDialect
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
    dialect = HexSLDialect.from_name(dialect_name)
    result_df = SnapshotTest.get_result_df(dialect)
    expected_df = SnapshotTest.get_expected_df(dialect)
    SnapshotTest.validate(expected_df, result_df, dialect)
