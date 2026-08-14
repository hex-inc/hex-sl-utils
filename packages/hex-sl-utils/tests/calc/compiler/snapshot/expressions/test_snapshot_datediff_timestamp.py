from __future__ import annotations

from datetime import datetime
import polars as pl
from hex_sl.dialect.base import HexSLDialect

from hex_sl_utils.datatype import DataType

from ..snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    columns = {
        "d1": DataType.TIMESTAMP,
        "d2": DataType.TIMESTAMP,
    }
    timezone = "America/New_York"

    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            "diffweeks(d1, d2)",
            "diffdays(d1, d2)",
            "diffhours(d1, d2)",
            "diffminutes(d1, d2)",
            "diffseconds(d1, d2)",
            "diffmilliseconds(d1, d2)",
        ]

    @classmethod
    def get_expression_input_data(cls) -> pl.DataFrame:
        df = pl.DataFrame(
            {
                "d1": [
                    datetime(2021, 1, 1, 1, 2, 23, 123000),
                    datetime(2022, 5, 15, 1, 2, 3, 456000),
                    datetime(2023, 12, 30, 1, 2, 3, 432000),
                    datetime(2024, 9, 12, 1, 2, 43, 321000),
                ],
                "d2": [
                    datetime(2021, 1, 2, 7, 3, 4, 987000),
                    datetime(2022, 2, 3, 0, 3, 1, 123000),
                    datetime(2023, 12, 31, 1, 2, 3, 456000),
                    datetime(2024, 10, 13, 1, 2, 3, 789000),
                ],
            }
        )
        return df

    @classmethod
    def get_expected_df_from_input(
        cls, expression_input_data: pl.DataFrame, dialect: HexSLDialect
    ) -> pl.DataFrame:
        df = expression_input_data
        diff_ms = df.select(
            pl.col("d2").dt.timestamp("ms") - pl.col("d1").dt.timestamp("ms")
        )

        expected_df = pl.DataFrame(
            {
                "row": [0, 1, 2, 3],
                "col1": df.select(diff_ms / (1000 * 60 * 60 * 24 * 7)),
                "col2": df.select(diff_ms / (1000 * 60 * 60 * 24)),
                "col3": df.select(diff_ms / (1000 * 60 * 60)),
                "col4": df.select(diff_ms / (1000 * 60)),
                "col5": df.select(diff_ms / 1000),
                "col6": df.select(diff_ms),
            }
        )
        return expected_df

    @classmethod
    def validate(
        cls, expected_df: pl.DataFrame, result_df: pl.DataFrame, dialect: HexSLDialect
    ) -> None:
        import polars.testing as pl_testing

        # Convert the result to the expected schema, to handle Decimals
        result_df = result_df.cast(expected_df.schema)

        print(dialect.name())
        pl_testing.assert_frame_equal(
            result_df, expected_df, check_dtypes=False, atol=1e-2
        )


# Database result tests

def test_snapshot_datediff_timestamp_validate(dialect_name):
    """Test datediff timestamp expressions for each dialect separately."""
    dialect = HexSLDialect.from_name(dialect_name)
    result_df = SnapshotTest.get_result_df(dialect, timezone="America/New_York")
    expected_df = SnapshotTest.get_expected_df(dialect)
    SnapshotTest.validate(expected_df, result_df, dialect)
