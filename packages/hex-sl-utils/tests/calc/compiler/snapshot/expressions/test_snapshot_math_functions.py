from __future__ import annotations

from hex_sl_utils.datatype import DataType

from ..snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    columns = {
        "int_col": DataType.NUMBER,
        "float_col": DataType.NUMBER,
        "trig_col": DataType.NUMBER,
    }

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
