from __future__ import annotations

import polars as pl

from hex_sl_utils.datatype import DataType
from hex_sl_utils.dialect import Dialect

from ..snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    columns = {
        "str_col1": DataType.STRING,
        "str_col2": DataType.STRING,
        "var_len_col": DataType.STRING,
        "replace_col": DataType.STRING,
    }

    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            "concat()",
            "concat(str_col1)",
            "concat(str_col1, ' ', str_col2)",
            "left(var_len_col, 2)",
            "right(var_len_col, 2)",
            "substitute(replace_col, 'cd', 'zz')",
            "substitute('abcde', 'cd', 'zz')",
            "lower(var_len_col)",
            "upper(str_col2)",
        ]

    @classmethod
    def get_expression_input_data(cls) -> pl.DataFrame:
        return pl.DataFrame(
            {
                "str_col1": ["a", "b", None, "d", None],
                "str_col2": ["x", None, "z", None, None],
                "var_len_col": ["A", "AB", "ABCD", "ABCDE", "XY"],
                "replace_col": ["abc", "abcd", "abcde", "abcdef", "xy"],
            }
        )

    @classmethod
    def get_expected_df_from_input(
        cls, expression_input_data: pl.DataFrame, dialect: Dialect
    ) -> pl.DataFrame:
        df = expression_input_data

        # Handle NULLs as empty strings for concat operations
        str_col1_filled = df["str_col1"].fill_null("")
        str_col2_filled = df["str_col2"].fill_null("")

        # Build expected results with NULL handling
        col3_values = []
        for i in range(len(df)):
            s1 = str_col1_filled[i]
            s2 = str_col2_filled[i]
            col3_values.append(f"{s1} {s2}")

        expected_df = pl.DataFrame(
            {
                "row": [0, 1, 2, 3, 4],
                "col1": [""] * 5,  # Empty string for concat()
                "col2": str_col1_filled,  # NULLs become empty strings
                "col3": col3_values,  # Concat with NULLs as empty strings
                "col4": df["var_len_col"].str.slice(0, 2),
                "col5": df["var_len_col"].str.slice(-2),
                "col6": df["replace_col"].str.replace("cd", "zz"),
                "col7": ["abzze"] * 5,
                "col8": df["var_len_col"].str.to_lowercase(),
                "col9": df["str_col2"].str.to_uppercase(),
            }
        )
        return expected_df


# Database result tests


def test_snapshot_string_functions1_validate(dialect_name):
    """Test string functions 1 validation for each dialect."""
    dialect = Dialect.from_name(dialect_name)
    result_df = SnapshotTest.get_result_df(dialect)
    expected_df = SnapshotTest.get_expected_df(dialect)
    SnapshotTest.validate(expected_df, result_df, dialect)
