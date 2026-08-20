from __future__ import annotations

import polars as pl
import pytest
from inline_snapshot import snapshot

from hex_sl_utils.datatype import DataType
from hex_sl_utils.dialect import Dialect

from ..snapshot_base import SelectionSnapshotTestBase

CASES = [
    # value, splitter, part_number
    ["a-b-c", "-", 1],
    ["a-b-c", "-", 2],
    ["a-b-c", "-", 3],
    ["a-b-c-d-e-f", "-", 3],
    ["a b c", " ", 2],
    ["a<>b<>c", "<>", 2],
    ["", "-", 1],
    ["a-b", "-", 4],
    [None, "-", 1],
]


class SnapshotTest(SelectionSnapshotTestBase):
    columns = {
        "values": DataType.STRING,
        "delimiter": DataType.STRING,
        "part_number": DataType.NUMBER,
    }

    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            "splitPart(values, 'NEVER', 1)",
            "delimiter",
            "part_number",
            "splitPart(values, delimiter, part_number)",
        ]

    @classmethod
    def get_expression_input_data(cls) -> pl.DataFrame:
        df = pl.DataFrame(
            {
                "values": [c[0] for c in CASES],
                "delimiter": [c[1] for c in CASES],
                "part_number": [c[2] for c in CASES],
            }
        )
        return df

    @classmethod
    def get_expected_df_from_input(
        cls, expression_input_data: pl.DataFrame, dialect: Dialect
    ) -> pl.DataFrame:
        def reference_impl(s: str, d: str, part: int):
            if not s:
                return s
            parts = s.split(d)
            part_idx = part - 1
            if part_idx >= len(parts):
                return ""
            return parts[part_idx]

        expected_df = pl.DataFrame(
            {
                "row": list(range(len(CASES))),
                "col1": [reference_impl(c[0], "NEVER", 1) for c in CASES],
                "col2": [c[1] for c in CASES],
                "col3": [c[2] for c in CASES],
                "col4": [reference_impl(*c) for c in CASES],
            }
        )
        return expected_df


# Database result tests


def test_snapshot_string_split_part_validate(dialect_name):
    """Test string split part expressions for each dialect separately."""
    dialect = Dialect.from_name(dialect_name)
    result_df = SnapshotTest.get_result_df(dialect)
    expected_df = SnapshotTest.get_expected_df(dialect)
    SnapshotTest.validate(expected_df, result_df, dialect)


@pytest.mark.database
@pytest.mark.database_local
def test_snapshot_string_split_part_result():
    """Test string split part expressions for each dialect separately."""
    dialect_name = "duckdb"
    dialect = Dialect.from_name(dialect_name)
    result_str = SnapshotTest.get_result_df_str(dialect)

    assert result_str == snapshot("""\
shape: (9, 5)
┌─────┬─────────────┬──────┬──────┬──────┐
│ row ┆ col1        ┆ col2 ┆ col3 ┆ col4 │
│ --- ┆ ---         ┆ ---  ┆ ---  ┆ ---  │
│ i32 ┆ str         ┆ str  ┆ i32  ┆ str  │
╞═════╪═════════════╪══════╪══════╪══════╡
│ 0   ┆ a-b-c       ┆ -    ┆ 1    ┆ a    │
│ 1   ┆ a-b-c       ┆ -    ┆ 2    ┆ b    │
│ 2   ┆ a-b-c       ┆ -    ┆ 3    ┆ c    │
│ 3   ┆ a-b-c-d-e-f ┆ -    ┆ 3    ┆ c    │
│ 4   ┆ a b c       ┆      ┆ 2    ┆ b    │
│ 5   ┆ a<>b<>c     ┆ <>   ┆ 2    ┆ b    │
│ 6   ┆             ┆ -    ┆ 1    ┆      │
│ 7   ┆ a-b         ┆ -    ┆ 4    ┆      │
│ 8   ┆ null        ┆ -    ┆ 1    ┆ null │
└─────┴─────────────┴──────┴──────┴──────┘\
""")
