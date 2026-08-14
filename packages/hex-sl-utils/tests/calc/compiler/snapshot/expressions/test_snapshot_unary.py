from __future__ import annotations

from hex_sl_utils.datatype import DataType

from ..snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    columns = {
        "numeric_col": DataType.NUMBER,
        "bool_col": DataType.BOOLEAN,
    }

    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            "-numeric_col",
            "+numeric_col",
            "!bool_col",
            "!!bool_col",
        ]
