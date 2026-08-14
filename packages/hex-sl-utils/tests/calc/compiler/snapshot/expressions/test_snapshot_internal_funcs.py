from __future__ import annotations

from tests.compiler.snapshots.snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        """Return calc expressions to test."""
        return [
            # _chart_toNumber tests
            "_chart_toNumber(str_int)",  # String to number
            "_chart_toNumber(str_float)",  # String float to number
            "_chart_toNumber(bool_col)",  # Boolean to number (1/0)
            "_chart_toNumber(date_col)",  # Date to epoch ms
            "_chart_toNumber(timestamp_col)",  # Timestamp to epoch ms
            "_chart_toNumber(int_col)",  # Number to number (no-op)
            "_chart_toNumber(float_col)",  # Float to float (no-op)
            # _chart_toDatetime tests
            "_chart_toDatetime(str_date)",  # String to datetime
            "_chart_toDatetime(str_datetime)",  # String datetime to datetime
            "_chart_toDatetime(epoch_ms)",  # Number to datetime
            "_chart_toDatetime(bool_col)",  # Boolean to datetime (via epoch)
            "_chart_toDatetime(date_col)",  # Date to timestamp
            "_chart_toDatetime(timestamp_col)",  # Timestamp to timestamp (no-op)
            # Combined tests
            "_chart_toNumber(_chart_toDatetime(str_date))",  # String -> datetime -> number
            "_chart_toDatetime(_chart_toNumber(bool_col))",  # Boolean -> number -> datetime
        ]
