from __future__ import annotations

from hex_sl_utils.datatype import DataType

from ..snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    columns = {
        "d": DataType.DATE,
    }

    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            "year(d)",
            "quarter(d)",
            "month(d)",
            "day(d)",
            "dayofweek(d)",
            "hour(d)",
            "minute(d)",
            "second(d)",
            "millisecond(d)",
        ]
