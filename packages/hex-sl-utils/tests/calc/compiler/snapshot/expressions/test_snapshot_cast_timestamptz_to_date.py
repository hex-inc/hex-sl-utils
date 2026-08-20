from __future__ import annotations

from hex_sl_utils.datatype import DataType

from ..snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    columns = {
        "tstz_col": DataType.TIMESTAMPTZ,
        "ts_col": DataType.TIMESTAMP,
    }
    timezone = "America/New_York"

    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            # TimestampTz To Date
            "todate(tstz_col)",
            # Timestamp To Date
            "todate(ts_col)",
        ]
