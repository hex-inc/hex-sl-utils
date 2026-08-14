from __future__ import annotations

import polars as pl
from hex_sl.dialect.base import HexSLDialect

from hex_sl_utils.datatype import DataType

from ..snapshot_base import AggregationSnapshotTestBase


class SnapshotTest(AggregationSnapshotTestBase):
    columns = {
        "int_col": DataType.NUMBER,
        "float_col": DataType.NUMBER,
    }
    support_method = "supports_percentile_exact"

    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            "percentile(int_col, 0.5)",
            "percentile(float_col, 0.75)",
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
        cls, expression_input_data: pl.DataFrame, dialect: HexSLDialect
    ) -> pl.DataFrame:
        df = expression_input_data
        expected_df = pl.DataFrame(
            {
                "col1": [df["int_col"].quantile(0.5)],
                "col2": [df["float_col"].quantile(0.75)],
            }
        )
        return expected_df


# Database result tests

def test_snapshot_percentile_exact_validate(dialect_name):
    """Test exact percentile aggregation validation for each dialect."""
    import pytest

    dialect = HexSLDialect.from_name(dialect_name)

    if not dialect.supports_percentile_exact():
        pytest.skip(f"Exact percentile is not supported by {dialect_name}")

    result_df = SnapshotTest.get_result_df(dialect)
    expected_df = SnapshotTest.get_expected_df(dialect)
    SnapshotTest.validate(expected_df, result_df, dialect)
