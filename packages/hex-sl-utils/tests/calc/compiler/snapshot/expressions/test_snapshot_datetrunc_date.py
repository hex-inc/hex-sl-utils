from __future__ import annotations

from tests.compiler.snapshots.snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
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
