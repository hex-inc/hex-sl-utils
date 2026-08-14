from __future__ import annotations

from tests.compiler.snapshots.snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            # Date To Timestamp
            "todatetime(date_col)",
            # Date To Timestamp With Timezone
            "todatetime(date_col, 'America/New_York')",
        ]
