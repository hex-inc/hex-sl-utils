from __future__ import annotations

from tests.compiler.snapshots.snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            "year(ts)",
            "quarter(ts)",
            "month(ts)",
            "day(ts)",
            "dayofweek(ts)",
            "hour(ts)",
            "minute(ts)",
            "second(ts)",
            "millisecond(ts)",
        ]
