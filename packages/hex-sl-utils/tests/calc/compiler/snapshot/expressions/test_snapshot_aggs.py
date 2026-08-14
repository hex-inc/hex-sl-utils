from __future__ import annotations

from hex_sl_utils.datatype import DataType

from ..snapshot_base import AggregationSnapshotTestBase


class SnapshotTest(AggregationSnapshotTestBase):
    columns = {
        "numeric_col": DataType.NUMBER,
        "var_col": DataType.NUMBER,
        "boolean_col": DataType.BOOLEAN,
        "boolean_num_col": DataType.NUMBER,
        "null_col": DataType.NUMBER,
    }

    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            "min(numeric_col)",
            "max(numeric_col)",
            "sum(numeric_col)",
            "mean(numeric_col)",
            "stddev(numeric_col)",
            "stddevpop(numeric_col)",
            "variance(var_col)",
            "variancepop(var_col)",
            "count()",
            "count(null_col)",
            "countdistinct(null_col)",
            "sumboolean(boolean_col)",
            "sumboolean(boolean_num_col)",
        ]
