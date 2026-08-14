from __future__ import annotations

from hex_sl_utils.datatype import DataType

from ..snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    columns = {
        "bool_col1": DataType.BOOLEAN,
        "bool_col2": DataType.BOOLEAN,
        "int_col": DataType.NUMBER,
    }

    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            # AND operations
            "bool_col1 AND bool_col2",
            "bool_col1 AND TRUE",
            "bool_col1 AND FALSE",
            # OR operations
            "bool_col1 OR bool_col2",
            "bool_col1 OR TRUE",
            "bool_col1 OR FALSE",
            # Mixed operations
            "(bool_col1 AND bool_col2) OR NOT bool_col1",
            "bool_col1 AND (int_col > 0)",
            "(bool_col1 AND bool_col2) == (bool_col1 OR bool_col2)",
        ]
