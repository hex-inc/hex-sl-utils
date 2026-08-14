from __future__ import annotations

import polars as pl
from hex_sl.dialect.base import HexSLDialect

from hex_sl_utils.datatype import DataType

from ..snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    columns = {
        "int_col1": DataType.NUMBER,
        "int_col2": DataType.NUMBER,
        "float_col": DataType.NUMBER,
        "pow_base": DataType.NUMBER,
        "pow_exp": DataType.NUMBER,
    }

    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            # Addition
            "int_col1 + int_col2",
            "float_col + int_col2",
            # Subtraction
            "int_col1 - int_col2",
            # Multiplication
            "int_col1 * int_col2 * 2",
            # Division (with zero handling)
            "int_col1 / int_col2",
            # Power
            "pow_base ^ pow_exp ^ 1",
            # Modulo
            r"int_col1 % int_col2",
            # Mixed operations
            "(int_col1 + float_col) * (int_col2 - 1) / 2",
        ]

    @classmethod
    def get_expression_input_data(cls) -> pl.DataFrame:
        return pl.DataFrame(
            {
                "int_col1": [-1, 10, -2, 2],
                "int_col2": [2, 0, -12, 2],
                "float_col": [-1.0, 10.5, -2.0, 2.0],
                "pow_base": [-1, 10, -2, 2],
                "pow_exp": [2, 2, 3, 4],
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
                "col1": df["int_col1"] + df["int_col2"],
                "col2": df["float_col"] + df["int_col2"],
                "col3": df["int_col1"] - df["int_col2"],
                "col4": df["int_col1"] * df["int_col2"] * 2,
                "col5": df.select(
                    pl.when(pl.col("int_col2") == 0)
                    .then(None)
                    .otherwise(pl.col("int_col1") / pl.col("int_col2"))
                ).to_series(),
                "col6": df["pow_base"] ** (df["pow_exp"] ** 1),
                # In Polars (and Python in general), the modulo operator returns a
                # result with the same sign as the denominator. However, in most SQL
                # implementations, the modulo operator returns a result with the
                # same sign as the numerator. So we'll compute the modulo manually
                # the way SQL
                "col7": df.select(
                    pl.when(pl.col("int_col2") == 0)
                    .then(None)
                    .otherwise(
                        (pl.col("int_col1") % pl.col("int_col2")).abs()
                        * pl.col("int_col1").sign()
                    )
                ).to_series(),
                "col8": (df["int_col1"] + df["float_col"]) * (df["int_col2"] - 1) / 2,
            }
        )
        return expected_df

    @classmethod
    def validate(
        cls,
        expected_df: pl.DataFrame,
        result_df: pl.DataFrame,
        dialect: HexSLDialect,
    ):
        import polars.testing as pl_testing
        from tests.compiler.util import floatify

        pl_testing.assert_frame_equal(
            floatify(result_df),
            expected_df,
            check_dtypes=False,
            rtol=1e-3,
        )


# Database result tests

def test_snapshot_binary_math_validate(dialect_name):
    """Test binary math validation for each dialect."""
    dialect = HexSLDialect.from_name(dialect_name)
    result_df = SnapshotTest.get_result_df(dialect)
    expected_df = SnapshotTest.get_expected_df(dialect)
    SnapshotTest.validate(expected_df, result_df, dialect)
