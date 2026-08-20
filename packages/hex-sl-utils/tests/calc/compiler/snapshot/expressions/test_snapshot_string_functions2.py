from __future__ import annotations

from hex_sl_utils.datatype import DataType

from ..snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    columns = {
        "var_len_col": DataType.STRING,
        "replace_col": DataType.STRING,
    }

    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            "length(var_len_col)",
            "contains(var_len_col, 'BC')",
            "startswith(var_len_col, 'ABC')",
            "endswith(replace_col, 'de')",
        ]
