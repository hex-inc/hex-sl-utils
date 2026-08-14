from __future__ import annotations

from tests.compiler.snapshots.snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            # String-to-number coercion: isoneof(number_col, "1", "2")
            'isoneof(int_col, "1", "2")',
            # Number-to-string coercion: isoneof(string_col, 1, 2)
            "isoneof(str_col, 1, 2)",
            # Mixed: some args match, some need coercion
            'isoneof(int_col, 1, "2", 3)',
            # String-to-date coercion: isoneof(date_col, "2021-01-01", "2021-01-02")
            'isoneof(date_col, "2021-01-01", "2021-01-02")',
            # Integer-to-boolean coercion: isoneof(bool_col, 1)
            "isoneof(bool_col, 1)",
            # No options → false literal
            "isoneof(int_col)",
        ]
