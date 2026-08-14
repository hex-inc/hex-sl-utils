from __future__ import annotations

from hex_sl_utils.datatype import DataType

from ..snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    columns = {
        "values": DataType.STRING,
        "delimiter": DataType.STRING,
        "part_number": DataType.NUMBER,
    }

    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            "splitPart(values, 'NEVER', 1)",
            "delimiter",
            "part_number",
            "splitPart(values, delimiter, part_number)",
        ]
