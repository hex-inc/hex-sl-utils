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
            "ts",
            "truncyear(ts)",
            "truncquarter(ts)",
            "truncmonth(ts)",
            "truncweek(ts)",
            "truncweekmonday(ts)",
            "truncday(ts)",
            "trunchour(ts)",
            "truncminute(ts)",
            "truncsecond(ts)",
            "truncmillisecond(ts)",
        ]
