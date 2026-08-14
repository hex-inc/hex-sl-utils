from __future__ import annotations

from tests.compiler.snapshots.snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            "concat()",
            "concat(str_col1)",
            "concat(str_col1, ' ', str_col2)",
            "left(var_len_col, 2)",
            "right(var_len_col, 2)",
            "substitute(replace_col, 'cd', 'zz')",
            "substitute('abcde', 'cd', 'zz')",
            "lower(var_len_col)",
            "upper(str_col2)",
        ]
