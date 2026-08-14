from __future__ import annotations

from tests.compiler.snapshots.snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            # TimestampTz To Date
            "toNumber(tstz_col < ToDatetime('2021-01-02 10:00:00'))",
            "toNumber(tstz_col < ToDate('2021-01-02'))",
        ]
