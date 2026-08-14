from __future__ import annotations

from tests.compiler.snapshots.snapshot_base import AggregationSnapshotTestBase


class SnapshotTest(AggregationSnapshotTestBase):
    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            "percentile(int_col, 0.5)",
            "percentile(float_col, 0.75)",
        ]
