from __future__ import annotations

from hex_sl_utils.datatype import DataType

from ..snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    columns = {
        "lhs": DataType.NUMBER,
        "rhs": DataType.NUMBER,
    }

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
