from __future__ import annotations

import polars as pl
import polars.testing as pl_testing

from hex_sl_utils.datatype import DataType
from hex_sl_utils.dialect import Dialect

from ..snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    columns = {
        "int_col": DataType.NUMBER,
        "float_col": DataType.NUMBER,
        "trig_col": DataType.NUMBER,
    }

    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            "abs(int_col)",
            "round(float_col)",
            "ceil(float_col)",
            "floor(float_col)",
            "sqrt(trig_col)",
            "exp(trig_col)",
            "sin(trig_col)",
            "cos(trig_col)",
            "tan(trig_col)",
            "cot(trig_col)",
        ]

    @classmethod
    def get_expression_input_data(cls) -> pl.DataFrame:
        df = pl.DataFrame(
            {
                "int_col": [-1, 1, -2, 2],
                "float_col": [1.1, 1.5, 2.1, 2.9],
                "trig_col": [0, 1, 2, 3],
                "cot_col": [0, 1, 2, 3],
            }
        )
        return df

    @classmethod
    def get_expected_df_from_input(
        cls, expression_input_data: pl.DataFrame, dialect: Dialect
    ) -> pl.DataFrame:
        """Get the expected results dataframe (computed in polars).

        Args:
            expression_input_data: The input data for the expressions
            dialect: The SQL dialect being tested

        Returns:
            pl.DataFrame: The expected results for validation
        """
        df = expression_input_data
        expected_df = pl.DataFrame(
            {
                "row": [0, 1, 2, 3],
                "col1": df["int_col"].abs(),
                "col2": df["float_col"].round(),
                "col3": df["float_col"].ceil(),
                "col4": df["float_col"].floor(),
                "col5": df["trig_col"].cast(pl.Float64).sqrt(),
                "col6": df["trig_col"].cast(pl.Float64).exp(),
                "col7": df["trig_col"].cast(pl.Float64).sin(),
                "col8": df["trig_col"].cast(pl.Float64).cos(),
                "col9": df["trig_col"].cast(pl.Float64).tan(),
                "col10": df.select(
                    pl.when(df["cot_col"] == 0)
                    .then(None)
                    .otherwise(1 / df["cot_col"].cast(pl.Float64).tan())
                ),
            }
        )
        return expected_df

    @classmethod
    def validate(
        cls, expected_df: pl.DataFrame, result_df: pl.DataFrame, dialect: Dialect
    ) -> None:
        """Validate the query results against expected values."""
        assert result_df.shape == (4, 11)
        pl_testing.assert_frame_equal(
            result_df, expected_df, check_dtypes=False, abs_tol=1e-6
        )


# Database result tests


def test_snapshot_math_functions_validate(dialect_name):
    """Test math functions expressions for each dialect separately."""
    dialect = Dialect.from_name(dialect_name)
    result_df = SnapshotTest.get_result_df(dialect)
    expected_df = SnapshotTest.get_expected_df(dialect)
    SnapshotTest.validate(expected_df, result_df, dialect)
