from __future__ import annotations

import polars as pl
import polars.testing as pl_testing
import pytest
from inline_snapshot import snapshot

from hex_sl_utils.datatype import DataType
from hex_sl_utils.dialect import Dialect

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
        cls, expression_input_data: pl.DataFrame, dialect: Dialect
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
        dialect: Dialect,
    ):
        from database.util import floatify

        pl_testing.assert_frame_equal(
            floatify(result_df),
            expected_df,
            check_dtypes=False,
            rel_tol=1e-3,
        )


# Database result tests


def test_snapshot_binary_math_validate(dialect_name):
    """Test binary math validation for each dialect."""
    dialect = Dialect.from_name(dialect_name)
    result_df = SnapshotTest.get_result_df(dialect)
    expected_df = SnapshotTest.get_expected_df(dialect)
    SnapshotTest.validate(expected_df, result_df, dialect)


@pytest.mark.database
@pytest.mark.database_local
def test_snapshot_binary_math_result():
    """Test binary math result output."""
    dialect = Dialect.from_name("duckdb")
    result_str = SnapshotTest.get_result_df_str(dialect)

    assert result_str == snapshot("""\
shape: (4, 9)
┌─────┬──────┬───────────────┬──────┬──────┬──────────┬───────┬──────┬────────┐
│ row ┆ col1 ┆ col2          ┆ col3 ┆ col4 ┆ col5     ┆ col6  ┆ col7 ┆ col8   │
│ --- ┆ ---  ┆ ---           ┆ ---  ┆ ---  ┆ ---      ┆ ---   ┆ ---  ┆ ---    │
│ i32 ┆ i32  ┆ decimal[12,1] ┆ i32  ┆ i32  ┆ f64      ┆ f64   ┆ i32  ┆ f64    │
╞═════╪══════╪═══════════════╪══════╪══════╪══════════╪═══════╪══════╪════════╡
│ 0   ┆ 1    ┆ 1.0           ┆ -3   ┆ -4   ┆ -0.5     ┆ 1.0   ┆ -1   ┆ -1.0   │
│ 1   ┆ 10   ┆ 10.5          ┆ 10   ┆ 0    ┆ null     ┆ 100.0 ┆ null ┆ -10.25 │
│ 2   ┆ -14  ┆ -14.0         ┆ 10   ┆ 48   ┆ 0.166667 ┆ -8.0  ┆ -2   ┆ 26.0   │
│ 3   ┆ 4    ┆ 4.0           ┆ 0    ┆ 8    ┆ 1.0      ┆ 16.0  ┆ 0    ┆ 2.0    │
└─────┴──────┴───────────────┴──────┴──────┴──────────┴───────┴──────┴────────┘\
""")
