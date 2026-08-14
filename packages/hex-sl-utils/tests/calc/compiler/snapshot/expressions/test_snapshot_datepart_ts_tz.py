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
            "year(ts_tz)",
            "quarter(ts_tz)",
            "month(ts_tz)",
            "day(ts_tz)",
            "dayofweek(ts_tz)",
            "hour(ts_tz)",
            "minute(ts_tz)",
            "second(ts_tz)",
            "millisecond(ts_tz)",
        ]
