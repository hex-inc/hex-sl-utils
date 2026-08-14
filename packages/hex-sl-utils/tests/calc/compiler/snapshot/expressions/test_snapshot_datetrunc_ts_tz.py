from __future__ import annotations

from hex_sl_utils.datatype import DataType

from ..snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    columns = {
        "ts_tz": DataType.TIMESTAMPTZ,
    }
    timezone = "America/New_York"

    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            "ts_tz",
            "truncyear(ts_tz)",
            "truncquarter(ts_tz)",
            "truncmonth(ts_tz)",
            "truncweek(ts_tz)",
            "truncweekmonday(ts_tz)",
            "truncday(ts_tz)",
            "trunchour(ts_tz)",
            "truncminute(ts_tz)",
            "truncsecond(ts_tz)",
            "truncmillisecond(ts_tz)",
        ]
