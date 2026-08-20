from __future__ import annotations

import polars as pl
import polars.testing as pl_testing
import pytest
from inline_snapshot import snapshot

from hex_sl_utils.datatype import DataType
from hex_sl_utils.dialect import Dialect

from ..snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    columns = {
        "var_len_col": DataType.STRING,
        "replace_col": DataType.STRING,
    }

    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            "length(var_len_col)",
            "contains(var_len_col, 'BC')",
            "startswith(var_len_col, 'ABC')",
            "endswith(replace_col, 'de')",
        ]

    @classmethod
    def get_expression_input_data(cls) -> pl.DataFrame:
        df = pl.DataFrame(
            {
                "var_len_col": ["A", "AB", "ABCD", "ABCDE"],
                "replace_col": ["abc", "abcde", "abcdede", "abcdef"],
            }
        )
        return df

    @classmethod
    def get_expected_df_from_input(
        cls, expression_input_data: pl.DataFrame, dialect: Dialect
    ) -> pl.DataFrame:
        df = expression_input_data
        expected_df = pl.DataFrame(
            {
                "row": [0, 1, 2, 3],
                "col1": df["var_len_col"].str.len_chars(),
                "col2": df["var_len_col"].str.contains("BC"),
                "col3": df["var_len_col"].str.starts_with("ABC"),
                "col4": df["replace_col"].str.ends_with("de"),
            }
        )
        return expected_df

    @classmethod
    def validate(
        cls, expected_df: pl.DataFrame, result_df: pl.DataFrame, dialect: Dialect
    ) -> None:
        assert result_df.shape == (4, 5)
        pl_testing.assert_frame_equal(result_df, expected_df, check_dtypes=False)


# Database result tests


def test_snapshot_string_functions2_validate(dialect_name):
    """Test string functions 2 expressions for each dialect separately."""
    dialect = Dialect.from_name(dialect_name)
    result_df = SnapshotTest.get_result_df(dialect)
    expected_df = SnapshotTest.get_expected_df(dialect)
    SnapshotTest.validate(expected_df, result_df, dialect)


@pytest.mark.database
@pytest.mark.database_local
def test_snapshot_string_functions2_result():
    """Test string functions 2 expressions for each dialect separately."""
    dialect_name = SnapshotTest.result_dialect
    dialect = Dialect.from_name(dialect_name)
    result_str = SnapshotTest.get_result_df_str(dialect)

    assert result_str == snapshot("""\
shape: (4, 5)
┌─────┬──────┬───────┬───────┬───────┐
│ row ┆ col1 ┆ col2  ┆ col3  ┆ col4  │
│ --- ┆ ---  ┆ ---   ┆ ---   ┆ ---   │
│ i32 ┆ i64  ┆ bool  ┆ bool  ┆ bool  │
╞═════╪══════╪═══════╪═══════╪═══════╡
│ 0   ┆ 1    ┆ false ┆ false ┆ false │
│ 1   ┆ 2    ┆ false ┆ false ┆ true  │
│ 2   ┆ 4    ┆ true  ┆ true  ┆ true  │
│ 3   ┆ 5    ┆ true  ┆ true  ┆ false │
└─────┴──────┴───────┴───────┴───────┘\
""")


# SQL expression snapshots


def test_snapshot_string_functions2_sql():
    """Snapshot directly compiled calc SQL for every supported dialect."""
    assert SnapshotTest.render_sql_snapshot() == snapshot("""\
-- === BIGQUERY ===
LENGTH(`var_len_col`);
INSTR(`var_len_col`, 'BC') > 0;
STARTS_WITH(`var_len_col`, 'ABC');
ENDS_WITH(`replace_col`, 'de');

-- === CLICKHOUSE ===
CHAR_LENGTH("var_len_col");
position("var_len_col", 'BC') <> 0;
startsWith("var_len_col", 'ABC');
endsWith("replace_col", 'de');

-- === DUCKDB ===
LENGTH("var_len_col");
CONTAINS("var_len_col", 'BC');
STARTS_WITH("var_len_col", 'ABC');
SUFFIX("replace_col", 'de');

-- === MSSQL ===
LEN(CONCAT('A', [var_len_col], 'Z')) - 2;
IIF(CHARINDEX('BC', [var_len_col]) > 0, 1, 0);
IIF(LEFT([var_len_col], LEN('ABC')) = 'ABC', 1, 0);
IIF(RIGHT([replace_col], LEN('de')) = 'de', 1, 0);

-- === MYSQL ===
CHAR_LENGTH(`var_len_col`);
LOCATE('BC', `var_len_col`) > 0;
LEFT(`var_len_col`, CHAR_LENGTH('ABC')) = 'ABC';
RIGHT(`replace_col`, CHAR_LENGTH('de')) = 'de';

-- === POSTGRES ===
LENGTH("var_len_col");
POSITION('BC' IN "var_len_col") > 0;
STARTS_WITH("var_len_col", 'ABC');
RIGHT("replace_col", LENGTH('de')) = 'de';

-- === REDSHIFT ===
LENGTH("var_len_col");
POSITION(CAST('BC' AS VARCHAR(MAX)) IN "var_len_col") > 0;
LEFT("var_len_col", LENGTH(CAST('ABC' AS VARCHAR(MAX)))) = CAST('ABC' AS VARCHAR(MAX));
RIGHT("replace_col", LENGTH(CAST('de' AS VARCHAR(MAX)))) = CAST('de' AS VARCHAR(MAX));

-- === SNOWFLAKE ===
LENGTH("var_len_col");
CONTAINS("var_len_col", 'BC');
STARTSWITH("var_len_col", 'ABC');
ENDSWITH("replace_col", 'de');

-- === SPARK ===
LENGTH(`var_len_col`);
CONTAINS(`var_len_col`, 'BC');
STARTSWITH(`var_len_col`, 'ABC');
ENDSWITH(`replace_col`, 'de');

-- === TRINO ===
LENGTH("var_len_col");
STRPOS("var_len_col", 'BC') > 0;
STARTS_WITH("var_len_col", 'ABC');
SUBSTRING("replace_col", -LENGTH('de')) = 'de';
""")
