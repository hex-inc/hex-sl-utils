from __future__ import annotations

from hex_sl_utils.datatype import DataType

from ..snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    columns = {
        "date_col": DataType.DATE,
    }
    timezone = "America/New_York"

    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            # Date To Timestamp
            "todatetime(date_col)",
            # Date To Timestamp With Timezone
            "todatetime(date_col, 'America/New_York')",
        ]
