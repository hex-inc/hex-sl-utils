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
    support_method = "supports_median"

    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            "median(int_col)",
            "median(float_col)",
        ]

    @classmethod
    def get_expression_input_data(cls) -> pl.DataFrame:
        return pl.DataFrame(
            {
                "int_col": [1, 3, 5, 700],
                "float_col": [1.1, 2.2, 3.3, 4.4],
            }
        )

    @classmethod
    def get_expected_df_from_input(
        cls, expression_input_data: pl.DataFrame, dialect: HexSLDialect
    ) -> pl.DataFrame:
        df = expression_input_data
        expected_df = pl.DataFrame(
            {
                "col1": [df["int_col"].median()],
                "col2": [df["float_col"].median()],
            }
        )
        return expected_df


# Database result tests

def test_snapshot_median_agg_validate(dialect_name):
    """Test median aggregation validation for each dialect."""
    import pytest

    dialect = HexSLDialect.from_name(dialect_name)

    # Skip tests for dialects that don't support median
    if not dialect.supports_median():
        pytest.skip(f"Median is not supported by {dialect_name}")

    result_df = SnapshotTest.get_result_df(dialect)
    expected_df = SnapshotTest.get_expected_df(dialect)
    SnapshotTest.validate(expected_df, result_df, dialect)
