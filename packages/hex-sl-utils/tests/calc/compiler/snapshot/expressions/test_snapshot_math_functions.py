from __future__ import annotations

from tests.compiler.snapshots.snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            "abs(int_col)",
            "round(float_col)",
            "ceil(float_col)",
            "floor(float_col)",
            "sqrt(trig_col)",
            "exp(trig_col)",
            "sin(trig_col)",
            "cos(trig_col)",
            "tan(trig_col)",
            "cot(trig_col)",
        ]
