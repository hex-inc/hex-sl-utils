from __future__ import annotations

from hex_sl_utils.datatype import DataType

from ..snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    columns = {
        "ts_string_col": DataType.STRING,
    }

    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            "todatetime(ts_string_col)",
        ]
