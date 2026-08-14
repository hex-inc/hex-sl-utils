from __future__ import annotations

from tests.compiler.snapshots.snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            "if(lhs > 0, lhs, -100)",
            "isnull(nullable)",
            "isoneof(lhs, 1, 2, 3)",
            # Testing isfinite on only finite values here so that we test all
            # dialects, even those that don't support non-finite values.
            # The behavior for dialects that do support non-finite values
            # is tested in test_snapshot_isfinite.py
            "isfinite(lhs)",
            # Switch function without default
            "switch(switch_input, 1, 'A', 2, 'B', 3, 'C')",
            # Switch function with default
            "switch(switch_input, 1, 'A', 2, 'B', 3, 'C', 'Other')",
        ]
