from __future__ import annotations

from tests.compiler.snapshots.snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            # Addition
            "int_col1 + int_col2",
            "float_col + int_col2",
            # Subtraction
            "int_col1 - int_col2",
            # Multiplication
            "int_col1 * int_col2 * 2",
            # Division (with zero handling)
            "int_col1 / int_col2",
            # Power
            "pow_base ^ pow_exp ^ 1",
            # Modulo
            r"int_col1 % int_col2",
            # Mixed operations
            "(int_col1 + float_col) * (int_col2 - 1) / 2",
        ]
