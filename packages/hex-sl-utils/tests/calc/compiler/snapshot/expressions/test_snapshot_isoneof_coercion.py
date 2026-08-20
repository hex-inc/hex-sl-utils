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
    dialect = Dialect.from_name(SnapshotTest.result_dialect)
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


# SQL expression snapshots


def test_snapshot_isoneof_coercion_sql():
    """Snapshot directly compiled calc SQL for every supported dialect."""
    assert SnapshotTest.render_sql_snapshot() == snapshot("""\
-- === BIGQUERY ===
`int_col` IN (SAFE_CAST('1' AS FLOAT64), SAFE_CAST('2' AS FLOAT64));
`str_col` IN (
  CASE
    WHEN FLOOR(1) = CEIL(1) AND 1 >= -2147483648 AND 1 <= 2147483647
    THEN CAST(CAST(TRUNC(1) AS INT64) AS STRING)
    ELSE CAST(1 AS STRING)
  END,
  CASE
    WHEN FLOOR(2) = CEIL(2) AND 2 >= -2147483648 AND 2 <= 2147483647
    THEN CAST(CAST(TRUNC(2) AS INT64) AS STRING)
    ELSE CAST(2 AS STRING)
  END
);
`int_col` IN (1, SAFE_CAST('2' AS FLOAT64), 3);
`date_col` IN (SAFE_CAST('2021-01-01' AS DATE), SAFE_CAST('2021-01-02' AS DATE));
`bool_col` IN (1 <> 0);
FALSE;

-- === CLICKHOUSE ===
"int_col" IN (
  accurateCastOrNull('1', 'Nullable(Float64)'),
  accurateCastOrNull('2', 'Nullable(Float64)')
);
"str_col" IN (
  CASE
    WHEN FLOOR(1) = CEIL(1) AND 1 >= -2147483648 AND 1 <= 2147483647
    THEN CAST(CAST(1 AS Nullable(Int32)) AS Nullable(String))
    ELSE CAST(1 AS Nullable(String))
  END,
  CASE
    WHEN FLOOR(2) = CEIL(2) AND 2 >= -2147483648 AND 2 <= 2147483647
    THEN CAST(CAST(2 AS Nullable(Int32)) AS Nullable(String))
    ELSE CAST(2 AS Nullable(String))
  END
);
"int_col" IN (1, accurateCastOrNull('2', 'Nullable(Float64)'), 3);
"date_col" IN (
  accurateCastOrNull('2021-01-01', 'Nullable(DATE)'),
  accurateCastOrNull('2021-01-02', 'Nullable(DATE)')
);
"bool_col" IN (1 <> 0);
FALSE;

-- === DUCKDB ===
"int_col" IN (TRY_CAST('1' AS DOUBLE), TRY_CAST('2' AS DOUBLE));
"str_col" IN (
  CASE
    WHEN FLOOR(1) = CEIL(1) AND 1 >= -2147483648 AND 1 <= 2147483647
    THEN CAST(CAST(1 AS INT) AS TEXT)
    ELSE CAST(1 AS TEXT)
  END,
  CASE
    WHEN FLOOR(2) = CEIL(2) AND 2 >= -2147483648 AND 2 <= 2147483647
    THEN CAST(CAST(2 AS INT) AS TEXT)
    ELSE CAST(2 AS TEXT)
  END
);
"int_col" IN (1, TRY_CAST('2' AS DOUBLE), 3);
"date_col" IN (TRY_CAST('2021-01-01' AS DATE), TRY_CAST('2021-01-02' AS DATE));
"bool_col" IN (1 <> 0);
FALSE;

-- === MSSQL ===
IIF([int_col] IN (TRY_CAST('1' AS FLOAT), TRY_CAST('2' AS FLOAT)), 1, 0);
IIF(
  [str_col] IN (
    CASE
      WHEN FLOOR(1) = CEILING(1) AND 1 >= -2147483648 AND 1 <= 2147483647
      THEN CAST(CAST(1 AS INTEGER) AS VARCHAR(MAX))
      ELSE CAST(1 AS VARCHAR(MAX))
    END,
    CASE
      WHEN FLOOR(2) = CEILING(2) AND 2 >= -2147483648 AND 2 <= 2147483647
      THEN CAST(CAST(2 AS INTEGER) AS VARCHAR(MAX))
      ELSE CAST(2 AS VARCHAR(MAX))
    END
  ),
  1,
  0
);
IIF([int_col] IN (1, TRY_CAST('2' AS FLOAT), 3), 1, 0);
IIF([date_col] IN (TRY_CAST('2021-01-01' AS DATE), TRY_CAST('2021-01-02' AS DATE)), 1, 0);
IIF([bool_col] IN (IIF(1 <> 0, 1, 0)), 1, 0);
IIF((1 = 0), 1, 0);

-- === MYSQL ===
`int_col` IN (
  CASE
    WHEN ('1' RLIKE '^[-+]?[0-9]*\\\\.?[0-9]+$')
    THEN CAST('1' AS DOUBLE)
    ELSE NULL
  END,
  CASE
    WHEN ('2' RLIKE '^[-+]?[0-9]*\\\\.?[0-9]+$')
    THEN CAST('2' AS DOUBLE)
    ELSE NULL
  END
);
`str_col` IN (
  CASE
    WHEN FLOOR(1) = CEIL(1) AND 1 >= -2147483648 AND 1 <= 2147483647
    THEN CAST(CAST(1 AS SIGNED) AS CHAR)
    ELSE CAST(1 AS CHAR)
  END,
  CASE
    WHEN FLOOR(2) = CEIL(2) AND 2 >= -2147483648 AND 2 <= 2147483647
    THEN CAST(CAST(2 AS SIGNED) AS CHAR)
    ELSE CAST(2 AS CHAR)
  END
);
`int_col` IN (
  1,
  CASE
    WHEN ('2' RLIKE '^[-+]?[0-9]*\\\\.?[0-9]+$')
    THEN CAST('2' AS DOUBLE)
    ELSE NULL
  END,
  3
);
`date_col` IN (CAST('2021-01-01' AS DATE), CAST('2021-01-02' AS DATE));
`bool_col` IN (1 <> 0);
FALSE;

-- === POSTGRES ===
"int_col" IN (
  CASE
    WHEN '1' ~ '^[-+]?[0-9]*\\.?[0-9]+$'
    THEN CAST('1' AS DOUBLE PRECISION)
    ELSE NULL
  END,
  CASE
    WHEN '2' ~ '^[-+]?[0-9]*\\.?[0-9]+$'
    THEN CAST('2' AS DOUBLE PRECISION)
    ELSE NULL
  END
);
"str_col" IN (
  CASE
    WHEN FLOOR(1) = CEIL(1) AND 1 >= -2147483648 AND 1 <= 2147483647
    THEN CAST(CAST(1 AS INT) AS VARCHAR)
    ELSE CAST(1 AS VARCHAR)
  END,
  CASE
    WHEN FLOOR(2) = CEIL(2) AND 2 >= -2147483648 AND 2 <= 2147483647
    THEN CAST(CAST(2 AS INT) AS VARCHAR)
    ELSE CAST(2 AS VARCHAR)
  END
);
"int_col" IN (
  1,
  CASE
    WHEN '2' ~ '^[-+]?[0-9]*\\.?[0-9]+$'
    THEN CAST('2' AS DOUBLE PRECISION)
    ELSE NULL
  END,
  3
);
"date_col" IN (
  CASE
    WHEN '2021-01-01' ~ '^\\d{4}-\\d{2}-\\d{2}$'
    THEN CAST('2021-01-01' AS DATE)
    ELSE NULL
  END,
  CASE
    WHEN '2021-01-02' ~ '^\\d{4}-\\d{2}-\\d{2}$'
    THEN CAST('2021-01-02' AS DATE)
    ELSE NULL
  END
);
"bool_col" IN (1 <> 0);
FALSE;

-- === REDSHIFT ===
"int_col" IN (
  CASE
    WHEN CAST('1' AS VARCHAR(MAX)) ~ '^[-+]?[0-9]*\\\\.?[0-9]+$'
    THEN CAST(CAST('1' AS VARCHAR(MAX)) AS DOUBLE PRECISION)
    ELSE NULL
  END,
  CASE
    WHEN CAST('2' AS VARCHAR(MAX)) ~ '^[-+]?[0-9]*\\\\.?[0-9]+$'
    THEN CAST(CAST('2' AS VARCHAR(MAX)) AS DOUBLE PRECISION)
    ELSE NULL
  END
);
"str_col" IN (
  CASE
    WHEN FLOOR(1) = CEIL(1) AND 1 >= -2147483648 AND 1 <= 2147483647
    THEN CAST(CAST(1 AS INTEGER) AS VARCHAR)
    ELSE CAST(1 AS VARCHAR)
  END,
  CASE
    WHEN FLOOR(2) = CEIL(2) AND 2 >= -2147483648 AND 2 <= 2147483647
    THEN CAST(CAST(2 AS INTEGER) AS VARCHAR)
    ELSE CAST(2 AS VARCHAR)
  END
);
"int_col" IN (
  1,
  CASE
    WHEN CAST('2' AS VARCHAR(MAX)) ~ '^[-+]?[0-9]*\\\\.?[0-9]+$'
    THEN CAST(CAST('2' AS VARCHAR(MAX)) AS DOUBLE PRECISION)
    ELSE NULL
  END,
  3
);
"date_col" IN (
  CASE
    WHEN CAST('2021-01-01' AS VARCHAR(MAX)) ~ '^\\\\d{4}-\\\\d{2}-\\\\d{2}$'
    THEN CAST(CAST('2021-01-01' AS VARCHAR(MAX)) AS DATE)
    ELSE NULL
  END,
  CASE
    WHEN CAST('2021-01-02' AS VARCHAR(MAX)) ~ '^\\\\d{4}-\\\\d{2}-\\\\d{2}$'
    THEN CAST(CAST('2021-01-02' AS VARCHAR(MAX)) AS DATE)
    ELSE NULL
  END
);
"bool_col" IN (1 <> 0);
FALSE;

-- === SNOWFLAKE ===
"int_col" IN (TRY_CAST('1' AS DOUBLE), TRY_CAST('2' AS DOUBLE));
"str_col" IN (
  CASE
    WHEN FLOOR(1) = CEIL(1) AND 1 >= -2147483648 AND 1 <= 2147483647
    THEN CAST(CAST(1 AS INT) AS VARCHAR)
    ELSE CAST(1 AS VARCHAR)
  END,
  CASE
    WHEN FLOOR(2) = CEIL(2) AND 2 >= -2147483648 AND 2 <= 2147483647
    THEN CAST(CAST(2 AS INT) AS VARCHAR)
    ELSE CAST(2 AS VARCHAR)
  END
);
"int_col" IN (1, TRY_CAST('2' AS DOUBLE), 3);
"date_col" IN (TRY_CAST('2021-01-01' AS DATE), TRY_CAST('2021-01-02' AS DATE));
"bool_col" IN (1 <> 0);
FALSE;

-- === SPARK ===
`int_col` IN (CAST('1' AS DOUBLE), CAST('2' AS DOUBLE));
`str_col` IN (
  CASE
    WHEN FLOOR(1) = CEIL(1) AND 1 >= -2147483648 AND 1 <= 2147483647
    THEN CAST(CAST(1 AS INT) AS STRING)
    ELSE CAST(1 AS STRING)
  END,
  CASE
    WHEN FLOOR(2) = CEIL(2) AND 2 >= -2147483648 AND 2 <= 2147483647
    THEN CAST(CAST(2 AS INT) AS STRING)
    ELSE CAST(2 AS STRING)
  END
);
`int_col` IN (1, CAST('2' AS DOUBLE), 3);
`date_col` IN (CAST('2021-01-01' AS DATE), CAST('2021-01-02' AS DATE));
`bool_col` IN (1 <> 0);
FALSE;

-- === TRINO ===
"int_col" IN (TRY_CAST('1' AS DOUBLE), TRY_CAST('2' AS DOUBLE));
"str_col" IN (
  CASE
    WHEN FLOOR(1) = CEIL(1) AND 1 >= -2147483648 AND 1 <= 2147483647
    THEN CAST(CAST(1 AS INTEGER) AS VARCHAR)
    ELSE CAST(1 AS VARCHAR)
  END,
  CASE
    WHEN FLOOR(2) = CEIL(2) AND 2 >= -2147483648 AND 2 <= 2147483647
    THEN CAST(CAST(2 AS INTEGER) AS VARCHAR)
    ELSE CAST(2 AS VARCHAR)
  END
);
"int_col" IN (1, TRY_CAST('2' AS DOUBLE), 3);
"date_col" IN (TRY_CAST('2021-01-01' AS DATE), TRY_CAST('2021-01-02' AS DATE));
"bool_col" IN (1 <> 0);
FALSE;
""")
