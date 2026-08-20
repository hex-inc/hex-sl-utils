from __future__ import annotations

from hex_sl_utils.datatype import DataType

from ..snapshot_base import AggregationSnapshotTestBase


class SnapshotTest(AggregationSnapshotTestBase):
    columns = {
        "int_col": DataType.NUMBER,
        "float_col": DataType.NUMBER,
    }
    support_method = "supports_median"

    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            "median(int_col)",
            "median(float_col)",
        ]
