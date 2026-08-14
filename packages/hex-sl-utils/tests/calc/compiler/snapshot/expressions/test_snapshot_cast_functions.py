from __future__ import annotations

from hex_sl_utils.datatype import DataType

from ..snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    columns = {
        "int_col": DataType.NUMBER,
        "float_col": DataType.NUMBER,
        "bool_col": DataType.BOOLEAN,
        "date_col": DataType.DATE,
        "datetime_col": DataType.TIMESTAMP,
        "string_col": DataType.STRING,
        "ts_string_col": DataType.STRING,
        "date_string_col": DataType.STRING,
    }
    timezone = "America/New_York"

    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            # To string casts
            "totext(int_col)",
            "totext(float_col)",
            "totext(bool_col)",
            "totext(date_col)",
            "totext(datetime_col)",
            # To boolean casts
            "toboolean(int_col)",
            "toboolean(string_col)",
            # To numeric casts
            "tonumber(string_col)",
            "tonumber(bool_col)",
            # Date parsing
            "todate(date_string_col)",
            "todatetime(ts_string_col)",
            "todatetime(ts_string_col, 'UTC')",
            "todatetime(ts_string_col, 'America/New_York')",
        ]
