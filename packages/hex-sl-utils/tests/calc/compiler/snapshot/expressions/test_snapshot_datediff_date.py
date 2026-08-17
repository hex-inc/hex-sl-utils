from __future__ import annotations

from datetime import date

import polars as pl
import polars.testing as pl_testing

from hex_sl_utils.datatype import DataType
from hex_sl_utils.dialect import Dialect

from ..snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    columns = {
        "d1": DataType.DATE,
        "d2": DataType.DATE,
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
                    date(2021, 1, 1),
                    date(2022, 5, 15),
                    date(2023, 12, 30),
                    date(2024, 9, 12),
                ],
                "d2": [
                    date(2021, 1, 2),
                    date(2022, 2, 3),
                    date(2023, 12, 31),
                    date(2024, 10, 13),
                ],
            }
        )
        return df

    @classmethod
    def get_expected_df_from_input(
        cls, expression_input_data: pl.DataFrame, dialect: Dialect
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
        cls, expected_df: pl.DataFrame, result_df: pl.DataFrame, dialect: Dialect
    ) -> None:
        # Convert the result to the expected schema, to handle Decimals
        result_df = result_df.cast(expected_df.schema)

        print(dialect.name())
        pl_testing.assert_frame_equal(
            result_df, expected_df, check_dtypes=False, abs_tol=1e-2
        )


# Database result tests


def test_snapshot_datediff_date_validate(dialect_name):
    """Test datediff date expressions for each dialect separately."""
    dialect = Dialect.from_name(dialect_name)
    result_df = SnapshotTest.get_result_df(dialect, timezone="America/New_York")
    expected_df = SnapshotTest.get_expected_df(dialect)
    SnapshotTest.validate(expected_df, result_df, dialect)
