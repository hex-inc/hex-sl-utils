from __future__ import annotations

import polars as pl
from hex_sl.dialect.base import HexSLDialect

from hex_sl_utils.datatype import DataType

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
        cls, expression_input_data: pl.DataFrame, dialect: HexSLDialect
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
    dialect = HexSLDialect.from_name(dialect_name)
    result_df = SnapshotTest.get_result_df(dialect)
    expected_df = SnapshotTest.get_expected_df(dialect)
    SnapshotTest.validate(expected_df, result_df, dialect)
