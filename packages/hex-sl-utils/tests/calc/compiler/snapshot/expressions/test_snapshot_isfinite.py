from __future__ import annotations

import polars as pl
import pytest
from inline_snapshot import snapshot

from hex_sl_utils.datatype import DataType
from hex_sl_utils.dialect import Dialect

from ..snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    columns = {
        "float_input": DataType.NUMBER,
        "int_input": DataType.NUMBER,
        "str_input": DataType.STRING,
    }

    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            "isfinite(float_input)",
            "isfinite(int_input)",
            "isfinite(str_input)",
        ]

    @classmethod
    def get_expression_input_data(cls) -> pl.DataFrame:
        df = pl.DataFrame(
            {
                "int_input": [2, 2, -12, 2],
                "str_input": ["a", "b", None, "d"],
                "float_input": [1.0, float("inf"), 3.0, float("nan")],
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
                "col1": pl.Series("col1", df["float_input"].is_finite()),
                "col2": pl.Series("col2", df["int_input"].is_finite()),
                "col3": pl.Series("col3", df["str_input"].is_not_null()),
            }
        )
        return expected_df


# Database result tests


def test_snapshot_isfinite_validate(dialect_name):
    """Test isfinite function expressions for each dialect separately."""
    dialect = Dialect.from_name(dialect_name)
    result_df = SnapshotTest.get_result_df(dialect)
    expected_df = SnapshotTest.get_expected_df(dialect)
    SnapshotTest.validate(expected_df, result_df, dialect)


@pytest.mark.database
@pytest.mark.database_local
def test_snapshot_isfinite_result():
    """Test isfinite function expressions for each dialect separately."""
    dialect_name = SnapshotTest.result_dialect
    dialect = Dialect.from_name(dialect_name)
    result_str = SnapshotTest.get_result_df_str(dialect)

    assert result_str == snapshot("""\
shape: (4, 4)
┌─────┬───────┬──────┬───────┐
│ row ┆ col1  ┆ col2 ┆ col3  │
│ --- ┆ ---   ┆ ---  ┆ ---   │
│ i32 ┆ bool  ┆ bool ┆ bool  │
╞═════╪═══════╪══════╪═══════╡
│ 0   ┆ true  ┆ true ┆ true  │
│ 1   ┆ false ┆ true ┆ true  │
│ 2   ┆ true  ┆ true ┆ false │
│ 3   ┆ false ┆ true ┆ true  │
└─────┴───────┴──────┴───────┘\
""")


# SQL expression snapshots


def test_snapshot_isfinite_sql():
    """Snapshot directly compiled calc SQL for every supported dialect."""
    assert SnapshotTest.render_sql_snapshot() == snapshot("""\
-- === BIGQUERY ===
NOT (
  `float_input` IS NULL
  OR IS_NAN(CAST(`float_input` AS FLOAT64))
  OR `float_input` = CAST('Infinity' AS FLOAT64)
  OR `float_input` = CAST('-Infinity' AS FLOAT64)
);
NOT (
  `int_input` IS NULL
  OR IS_NAN(CAST(`int_input` AS FLOAT64))
  OR `int_input` = CAST('Infinity' AS FLOAT64)
  OR `int_input` = CAST('-Infinity' AS FLOAT64)
);
NOT `str_input` IS NULL;

-- === CLICKHOUSE ===
NOT (
  "float_input" IS NULL
  OR isNaN(CAST("float_input" AS Nullable(Float64)))
  OR "float_input" = CAST('Infinity' AS Nullable(Float64))
  OR "float_input" = CAST('-Infinity' AS Nullable(Float64))
);
NOT (
  "int_input" IS NULL
  OR isNaN(CAST("int_input" AS Nullable(Float64)))
  OR "int_input" = CAST('Infinity' AS Nullable(Float64))
  OR "int_input" = CAST('-Infinity' AS Nullable(Float64))
);
NOT (
  "str_input" IS NULL
);

-- === DUCKDB ===
NOT (
  "float_input" IS NULL OR ISNAN("float_input") OR ISINF("float_input")
);
NOT (
  "int_input" IS NULL OR ISNAN("int_input") OR ISINF("int_input")
);
NOT "str_input" IS NULL;

-- === MSSQL ===
IIF(NOT [float_input] IS NULL, 1, 0);
IIF(NOT [int_input] IS NULL, 1, 0);
IIF(NOT [str_input] IS NULL, 1, 0);

-- === MYSQL ===
NOT `float_input` IS NULL;
NOT `int_input` IS NULL;
NOT `str_input` IS NULL;

-- === POSTGRES ===
NOT (
  "float_input" IS NULL
  OR CAST("float_input" AS DOUBLE PRECISION) = CAST('NaN' AS DOUBLE PRECISION)
  OR "float_input" = CAST('Infinity' AS DOUBLE PRECISION)
  OR "float_input" = CAST('-Infinity' AS DOUBLE PRECISION)
);
NOT (
  "int_input" IS NULL
  OR CAST("int_input" AS DOUBLE PRECISION) = CAST('NaN' AS DOUBLE PRECISION)
  OR "int_input" = CAST('Infinity' AS DOUBLE PRECISION)
  OR "int_input" = CAST('-Infinity' AS DOUBLE PRECISION)
);
NOT "str_input" IS NULL;

-- === REDSHIFT ===
NOT (
  "float_input" IS NULL
  OR CAST("float_input" AS DOUBLE PRECISION) = CAST('NaN' AS DOUBLE PRECISION)
  OR "float_input" = CAST('Infinity' AS DOUBLE PRECISION)
  OR "float_input" = CAST('-Infinity' AS DOUBLE PRECISION)
);
NOT (
  "int_input" IS NULL
  OR CAST("int_input" AS DOUBLE PRECISION) = CAST('NaN' AS DOUBLE PRECISION)
  OR "int_input" = CAST('Infinity' AS DOUBLE PRECISION)
  OR "int_input" = CAST('-Infinity' AS DOUBLE PRECISION)
);
NOT "str_input" IS NULL;

-- === SNOWFLAKE ===
NOT (
  "float_input" IS NULL
  OR CAST("float_input" AS DOUBLE) = CAST('NaN' AS DOUBLE)
  OR "float_input" = CAST('Infinity' AS DOUBLE)
  OR "float_input" = CAST('-Infinity' AS DOUBLE)
);
NOT (
  "int_input" IS NULL
  OR CAST("int_input" AS DOUBLE) = CAST('NaN' AS DOUBLE)
  OR "int_input" = CAST('Infinity' AS DOUBLE)
  OR "int_input" = CAST('-Infinity' AS DOUBLE)
);
NOT "str_input" IS NULL;

-- === SPARK ===
NOT (
  `float_input` IS NULL
  OR ISNAN(CAST(`float_input` AS DOUBLE))
  OR `float_input` = CAST('Infinity' AS DOUBLE)
  OR `float_input` = CAST('-Infinity' AS DOUBLE)
);
NOT (
  `int_input` IS NULL
  OR ISNAN(CAST(`int_input` AS DOUBLE))
  OR `int_input` = CAST('Infinity' AS DOUBLE)
  OR `int_input` = CAST('-Infinity' AS DOUBLE)
);
NOT `str_input` IS NULL;

-- === TRINO ===
NOT (
  "float_input" IS NULL
  OR IS_NAN(CAST("float_input" AS DOUBLE))
  OR "float_input" = CAST('Infinity' AS DOUBLE)
  OR "float_input" = CAST('-Infinity' AS DOUBLE)
);
NOT (
  "int_input" IS NULL
  OR IS_NAN(CAST("int_input" AS DOUBLE))
  OR "int_input" = CAST('Infinity' AS DOUBLE)
  OR "int_input" = CAST('-Infinity' AS DOUBLE)
);
NOT "str_input" IS NULL;
""")
