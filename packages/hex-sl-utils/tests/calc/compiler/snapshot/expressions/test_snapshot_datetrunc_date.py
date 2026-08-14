from __future__ import annotations

from hex_sl_utils.datatype import DataType

from ..snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    columns = {
        "d": DataType.DATE,
    }
    timezone = "America/New_York"

    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            "d",
            "truncyear(d)",
            "truncquarter(d)",
            "truncmonth(d)",
            "truncweek(d)",
            "truncweekmonday(d)",
            "truncday(d)",
            "trunchour(d)",
            "truncminute(d)",
            "truncsecond(d)",
            "truncmillisecond(d)",
        ]
