from __future__ import annotations

from tests.compiler.snapshots.snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            "year(ts_tz)",
            "quarter(ts_tz)",
            "month(ts_tz)",
            "day(ts_tz)",
            "dayofweek(ts_tz)",
            "hour(ts_tz)",
            "minute(ts_tz)",
            "second(ts_tz)",
            "millisecond(ts_tz)",
        ]
