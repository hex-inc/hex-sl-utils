from __future__ import annotations

from datetime import date

import polars as pl
import polars.testing as pl_testing

from hex_sl_utils.datatype import DataType
from hex_sl_utils.dialect import Dialect

from ..snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    columns = {
        "d": DataType.DATE,
    }
    timezone = "America/New_York"

    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            "d",
            "truncyear(d)",
            "truncquarter(d)",
            "truncmonth(d)",
            "truncweek(d)",
            "truncweekmonday(d)",
            "truncday(d)",
            "trunchour(d)",
            "truncminute(d)",
            "truncsecond(d)",
            "truncmillisecond(d)",
        ]

    @classmethod
    def get_expression_input_data(cls) -> pl.DataFrame:
        df = pl.DataFrame(
            {
                "d": [
                    date(2021, 1, 1),
                    date(2022, 5, 15),
                    date(2023, 12, 30),
                    date(2024, 9, 12),
                ]
            }
        )
        return df

    @classmethod
    def get_expected_df_from_input(
        cls, expression_input_data: pl.DataFrame, dialect: Dialect
    ) -> pl.DataFrame:
        df = expression_input_data
        expected_df = pl.DataFrame(
            {
                "row": [0, 1, 2, 3],
                "col1": df["d"],
                "col2": df.select(pl.col("d").dt.truncate("1y")),
                "col3": df.select(pl.col("d").dt.truncate("1q")),
                "col4": df.select(pl.col("d").dt.truncate("1mo")),
                "col5": df.select(
                    # Truncate to Sunday-based week
                    pl.col("d")
                    - pl.duration(days=pl.col("d").dt.weekday() % 7 + 1)
                    + pl.duration(days=1)
                ),
                "col6": df.select(pl.col("d").dt.truncate("1w")),
                "col7": df.select(pl.col("d").dt.truncate("1d")),
                "col8": df["d"],
                "col9": df["d"],
                "col10": df["d"],
                "col11": df["d"],
            }
        )
        return expected_df

    @classmethod
    def validate(
        cls, expected_df: pl.DataFrame, result_df: pl.DataFrame, dialect: Dialect
    ) -> None:
        assert result_df.shape == (4, 12)
        pl_testing.assert_frame_equal(
            result_df, expected_df, check_dtypes=False, abs_tol=1e-6
        )


# Database result tests


def test_snapshot_datetrunc_date_validate(dialect_name):
    """Test datetrunc date expressions for each dialect separately."""
    dialect = Dialect.from_name(dialect_name)
    result_df = SnapshotTest.get_result_df(dialect)
    expected_df = SnapshotTest.get_expected_df(dialect)
    SnapshotTest.validate(expected_df, result_df, dialect)
