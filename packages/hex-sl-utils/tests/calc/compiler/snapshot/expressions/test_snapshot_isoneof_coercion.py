from __future__ import annotations

from datetime import date

import polars as pl
import pytest
from inline_snapshot import snapshot

from hex_sl_utils.datatype import DataType
from hex_sl_utils.dialect import Dialect

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

    @classmethod
    def get_expression_input_data(cls) -> pl.DataFrame:
        return pl.DataFrame(
            {
                "int_col": [1, 2, 3, 4],
                "str_col": ["1", "2", "3", "4"],
                "date_col": [
                    date(2021, 1, 1),
                    date(2021, 1, 2),
                    date(2021, 1, 3),
                    date(2021, 1, 4),
                ],
                "bool_col": [True, False, True, False],
            }
        )

    @classmethod
    def get_expected_df_from_input(
        cls, expression_input_data: pl.DataFrame, dialect: Dialect
    ) -> pl.DataFrame:
        df = expression_input_data
        return pl.DataFrame(
            {
                "row": [0, 1, 2, 3],
                # isoneof(int_col, "1", "2") → int_col in [1, 2]
                "col1": df["int_col"].is_in([1, 2]),
                # isoneof(str_col, 1, 2) → str_col in ["1", "2"]
                "col2": df["str_col"].is_in(["1", "2"]),
                # isoneof(int_col, 1, "2", 3) → int_col in [1, 2, 3]
                "col3": df["int_col"].is_in([1, 2, 3]),
                # isoneof(date_col, "2021-01-01", "2021-01-02") → date_col in [date(2021,1,1), date(2021,1,2)]
                "col4": df["date_col"].is_in([date(2021, 1, 1), date(2021, 1, 2)]),
                # isoneof(bool_col, 1) → bool_col in [True]
                "col5": df["bool_col"].is_in([True]),
                # isoneof(int_col) → always false
                "col6": pl.Series([False, False, False, False]),
            }
        )


# Database result tests


def test_snapshot_isoneof_coercion_validate(dialect_name):
    """Test isoneof coercion validation for each dialect."""
    dialect = Dialect.from_name(dialect_name)
    result_df = SnapshotTest.get_result_df(dialect)
    expected_df = SnapshotTest.get_expected_df(dialect)
    SnapshotTest.validate(expected_df, result_df, dialect)


@pytest.mark.database
@pytest.mark.database_local
def test_snapshot_isoneof_coercion_result():
    """Test isoneof coercion result output."""
    dialect = Dialect.from_name("duckdb")
    result_str = SnapshotTest.get_result_df_str(dialect)

    assert result_str == snapshot("""\
shape: (4, 7)
┌─────┬───────┬───────┬───────┬───────┬───────┬───────┐
│ row ┆ col1  ┆ col2  ┆ col3  ┆ col4  ┆ col5  ┆ col6  │
│ --- ┆ ---   ┆ ---   ┆ ---   ┆ ---   ┆ ---   ┆ ---   │
│ i32 ┆ bool  ┆ bool  ┆ bool  ┆ bool  ┆ bool  ┆ bool  │
╞═════╪═══════╪═══════╪═══════╪═══════╪═══════╪═══════╡
│ 0   ┆ true  ┆ true  ┆ true  ┆ true  ┆ true  ┆ false │
│ 1   ┆ true  ┆ true  ┆ true  ┆ true  ┆ false ┆ false │
│ 2   ┆ false ┆ false ┆ true  ┆ false ┆ true  ┆ false │
│ 3   ┆ false ┆ false ┆ false ┆ false ┆ false ┆ false │
└─────┴───────┴───────┴───────┴───────┴───────┴───────┘\
""")
