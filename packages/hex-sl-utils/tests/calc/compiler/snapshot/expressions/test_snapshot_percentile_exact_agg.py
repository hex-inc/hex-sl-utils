from __future__ import annotations

from hex_sl_utils.datatype import DataType

from ..snapshot_base import AggregationSnapshotTestBase


class SnapshotTest(AggregationSnapshotTestBase):
    columns = {
        "int_col": DataType.NUMBER,
        "float_col": DataType.NUMBER,
    }
    support_method = "supports_percentile_exact"

    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            "percentile(int_col, 0.5)",
            "percentile(float_col, 0.75)",
        ]
