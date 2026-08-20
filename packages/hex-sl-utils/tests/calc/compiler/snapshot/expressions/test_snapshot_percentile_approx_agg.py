from __future__ import annotations

import polars as pl
import polars.testing as pl_testing
import pytest
from inline_snapshot import snapshot

from hex_sl_utils.datatype import DataType
from hex_sl_utils.dialect import Dialect

from ..snapshot_base import AggregationSnapshotTestBase


class SnapshotTest(AggregationSnapshotTestBase):
    columns = {
        "int_col": DataType.NUMBER,
        "float_col": DataType.NUMBER,
    }
    support_method = "supports_percentile_approx"

    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            "percentileapprox(int_col, 0.5)",
            "percentileapprox(float_col, 0.75)",
        ]

    @classmethod
    def get_expression_input_data(cls) -> pl.DataFrame:
        return pl.DataFrame(
            {
                "int_col": [10, 20, 30, 40, 50],
                "float_col": [1.0, 2.0, 3.0, 4.0, 5.0],
            }
        )

    @classmethod
    def get_expected_df_from_input(
        cls, expression_input_data: pl.DataFrame, dialect: Dialect
    ) -> pl.DataFrame:
        df = expression_input_data
        expected_df = pl.DataFrame(
            {
                "col1": [df["int_col"].quantile(0.5)],
                "col2": [df["float_col"].quantile(0.75)],
            }
        )
        return expected_df

    @classmethod
    def validate(
        cls, expected_df: pl.DataFrame, result_df: pl.DataFrame, dialect: Dialect
    ) -> None:
        from hex_sl_utils.dialect.redshift import Redshift

        if isinstance(dialect, Redshift):
            expected_df = expected_df.select(
                **{col.lower(): expected_df[col] for col in expected_df.columns}
            )

        pl_testing.assert_frame_equal(
            result_df,
            expected_df,
            check_dtypes=False,
            abs_tol=0.5,
            check_column_order=True,
        )


# Database result tests


def test_snapshot_percentile_approx_validate(dialect_name):
    """Test approximate percentile aggregation validation for each dialect."""
    dialect = Dialect.from_name(dialect_name)

    if not dialect.supports_percentile_approx():
        pytest.skip(f"Approximate percentile is not supported by {dialect_name}")

    result_df = SnapshotTest.get_result_df(dialect)
    expected_df = SnapshotTest.get_expected_df(dialect)
    SnapshotTest.validate(expected_df, result_df, dialect)


@pytest.mark.database
@pytest.mark.database_local
def test_snapshot_percentile_approx_result():
    """Test approximate percentile aggregation result output."""
    dialect = Dialect.from_name("clickhouse")
    result_str = SnapshotTest.get_result_df_str(dialect)

    assert result_str == snapshot("""\
shape: (1, 2)
┌──────┬──────┐
│ col1 ┆ col2 │
│ ---  ┆ ---  │
│ f64  ┆ f64  │
╞══════╪══════╡
│ 30.0 ┆ 4.0  │
└──────┴──────┘\
""")
