from __future__ import annotations

from tests.compiler.snapshots.snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            "lhs < rhs",
            "lhs <= rhs",
            "lhs <= rhs",
            "lhs > rhs",
            "lhs >= rhs",
            "lhs >= rhs",
            "lhs == rhs",
            "lhs != rhs",
            "lhs != rhs",
        ]
