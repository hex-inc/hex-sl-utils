from __future__ import annotations

from tests.compiler.snapshots.snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            "ts",
            "truncyear(ts)",
            "truncquarter(ts)",
            "truncmonth(ts)",
            "truncweek(ts)",
            "truncweekmonday(ts)",
            "truncday(ts)",
            "trunchour(ts)",
            "truncminute(ts)",
            "truncsecond(ts)",
            "truncmillisecond(ts)",
        ]
