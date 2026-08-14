from __future__ import annotations

from tests.compiler.snapshots.snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            # To string casts
            "totext(int_col)",
            "totext(float_col)",
            "totext(bool_col)",
            "totext(date_col)",
            "totext(datetime_col)",
            # To boolean casts
            "toboolean(int_col)",
            "toboolean(string_col)",
            # To numeric casts
            "tonumber(string_col)",
            "tonumber(bool_col)",
            # Date parsing
            "todate(date_string_col)",
            "todatetime(ts_string_col)",
            "todatetime(ts_string_col, 'UTC')",
            "todatetime(ts_string_col, 'America/New_York')",
        ]
