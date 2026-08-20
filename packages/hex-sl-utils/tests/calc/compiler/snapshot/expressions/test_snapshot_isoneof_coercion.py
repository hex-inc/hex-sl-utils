from __future__ import annotations

from hex_sl_utils.datatype import DataType

from ..snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    columns = {
        "int_col": DataType.NUMBER,
        "str_col": DataType.STRING,
        "date_col": DataType.DATE,
        "bool_col": DataType.BOOLEAN,
    }

    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            # String-to-number coercion: isoneof(number_col, "1", "2")
            'isoneof(int_col, "1", "2")',
            # Number-to-string coercion: isoneof(string_col, 1, 2)
            "isoneof(str_col, 1, 2)",
            # Mixed: some args match, some need coercion
            'isoneof(int_col, 1, "2", 3)',
            # String-to-date coercion: isoneof(date_col, "2021-01-01", "2021-01-02")
            'isoneof(date_col, "2021-01-01", "2021-01-02")',
            # Integer-to-boolean coercion: isoneof(bool_col, 1)
            "isoneof(bool_col, 1)",
            # No options → false literal
            "isoneof(int_col)",
        ]
