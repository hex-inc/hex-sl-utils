from __future__ import annotations

from hex_sl_utils.datatype import DataType

from ..snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    columns = {
        "ts": DataType.TIMESTAMP,
    }

    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            "year(ts)",
            "quarter(ts)",
            "month(ts)",
            "day(ts)",
            "dayofweek(ts)",
            "hour(ts)",
            "minute(ts)",
            "second(ts)",
            "millisecond(ts)",
        ]
