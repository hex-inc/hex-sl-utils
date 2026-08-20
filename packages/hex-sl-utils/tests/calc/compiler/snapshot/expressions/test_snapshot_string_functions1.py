from __future__ import annotations

from hex_sl_utils.datatype import DataType

from ..snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    columns = {
        "str_col1": DataType.STRING,
        "str_col2": DataType.STRING,
        "var_len_col": DataType.STRING,
        "replace_col": DataType.STRING,
    }

    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            "concat()",
            "concat(str_col1)",
            "concat(str_col1, ' ', str_col2)",
            "left(var_len_col, 2)",
            "right(var_len_col, 2)",
            "substitute(replace_col, 'cd', 'zz')",
            "substitute('abcde', 'cd', 'zz')",
            "lower(var_len_col)",
            "upper(str_col2)",
        ]
