from __future__ import annotations

from hex_sl_utils.datatype import DataType

from ..snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    columns = {
        "float_input": DataType.NUMBER,
        "int_input": DataType.NUMBER,
        "str_input": DataType.STRING,
    }

    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            "isfinite(float_input)",
            "isfinite(int_input)",
            "isfinite(str_input)",
        ]
