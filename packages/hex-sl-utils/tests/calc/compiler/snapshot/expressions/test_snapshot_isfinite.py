from __future__ import annotations

import polars as pl

from hex_sl_utils.datatype import DataType
from hex_sl_utils.dialect import Dialect

from ..snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    columns = {
        "float_input": DataType.NUMBER,
        "int_input": DataType.NUMBER,
        "str_input": DataType.STRING,
    }

    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            "isfinite(float_input)",
            "isfinite(int_input)",
            "isfinite(str_input)",
        ]

    @classmethod
    def get_expression_input_data(cls) -> pl.DataFrame:
        df = pl.DataFrame(
            {
                "int_input": [2, 2, -12, 2],
                "str_input": ["a", "b", None, "d"],
                "float_input": [1.0, float("inf"), 3.0, float("nan")],
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
                "col1": pl.Series("col1", df["float_input"].is_finite()),
                "col2": pl.Series("col2", df["int_input"].is_finite()),
                "col3": pl.Series("col3", df["str_input"].is_not_null()),
            }
        )
        return expected_df


# Database result tests


def test_snapshot_isfinite_validate(dialect_name):
    """Test isfinite function expressions for each dialect separately."""
    dialect = Dialect.from_name(dialect_name)
    result_df = SnapshotTest.get_result_df(dialect)
    expected_df = SnapshotTest.get_expected_df(dialect)
    SnapshotTest.validate(expected_df, result_df, dialect)
