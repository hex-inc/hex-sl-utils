from __future__ import annotations

from tests.compiler.snapshots.snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            "year(d)",
            "quarter(d)",
            "month(d)",
            "day(d)",
            "dayofweek(d)",
            "hour(d)",
            "minute(d)",
            "second(d)",
            "millisecond(d)",
        ]
