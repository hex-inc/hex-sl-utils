from __future__ import annotations

from hex_sl_utils.datatype import DataType

from ..snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    columns = {
        "ts": DataType.TIMESTAMP,
        "d": DataType.DATE,
        "ts_tz": DataType.TIMESTAMPTZ,
    }
    timezone = "America/New_York"

    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            "datetimetoepochms(d)",
            "datetimetoepochms(ts)",
            "datetimetoepochms(ts_tz)",
            "epochmstodatetime(datetimetoepochms(d))",
            "epochmstodatetime(datetimetoepochms(ts))",
            "epochmstodatetime(datetimetoepochms(ts_tz))",
        ]
