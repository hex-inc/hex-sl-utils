from __future__ import annotations

from tests.compiler.snapshots.snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            "length(var_len_col)",
            "contains(var_len_col, 'BC')",
            "startswith(var_len_col, 'ABC')",
            "endswith(replace_col, 'de')",
        ]
