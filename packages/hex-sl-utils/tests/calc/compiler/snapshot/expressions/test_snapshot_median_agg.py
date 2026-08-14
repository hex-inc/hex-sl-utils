from __future__ import annotations

from tests.compiler.snapshots.snapshot_base import AggregationSnapshotTestBase


class SnapshotTest(AggregationSnapshotTestBase):
    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            "median(int_col)",
            "median(float_col)",
        ]
