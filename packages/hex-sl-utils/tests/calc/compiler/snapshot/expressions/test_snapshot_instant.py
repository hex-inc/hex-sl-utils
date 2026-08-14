from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo
import polars as pl
from hex_sl.dialect.base import HexSLDialect

from ..snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    columns = {}
    timezone = "America/New_York"

    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            "today()",
            "now()",
        ]

    @classmethod
    def get_expression_input_data(cls) -> pl.DataFrame:
        df = pl.DataFrame(
            {
                "idx": range(2),
            }
        )
        return df

    @classmethod
    def get_expected_df_from_input(
        cls, expression_input_data: pl.DataFrame, dialect: HexSLDialect
    ) -> pl.DataFrame:
        # Note: We can't create exact expected values for instant functions
        # We'll use the validation method instead
        df = expression_input_data
        expected_df = pl.DataFrame(
            {
                "row": df["idx"],
                "col1": [None, None],  # Placeholder for today()
                "col2": [None, None],  # Placeholder for now()
            }
        )
        return expected_df

    @classmethod
    def validate(
        cls, expected_df: pl.DataFrame, result_df: pl.DataFrame, dialect: HexSLDialect
    ) -> None:
        """Validate the query results against expected values with custom logic.

        Args:
            expected_df: The expected results dataframe (not used for instant functions)
            result_df: The actual results from executing the query
            dialect: The SQL dialect that was used
        """
        timezone = "America/New_York"

        # Get the current date and time
        now = datetime.now(tz=ZoneInfo(timezone))
        today = now.date()

        # Check if the 'today()' result is within 1 day of the current date
        assert result_df.select((pl.col("col1") - today).abs() <= pl.duration(days=1))[
            "col1"
        ].all(), "today() function is not within 1 day of the current date"

        # Check if the 'now()' result is within 1 minute of the current time
        assert result_df.select(
            (result_df["col2"] - pl.lit(now)).abs() < pl.duration(minutes=1)
        )["col2"].all(), "now() function is not within 1 minute of the current time"


# Database result tests

def test_snapshot_instant_validate(dialect_name):
    """Test instant function expressions for each dialect separately."""
    dialect = HexSLDialect.from_name(dialect_name)
    result_df = SnapshotTest.get_result_df(dialect, timezone="America/New_York")
    expected_df = SnapshotTest.get_expected_df(dialect)
    SnapshotTest.validate(expected_df, result_df, dialect)
