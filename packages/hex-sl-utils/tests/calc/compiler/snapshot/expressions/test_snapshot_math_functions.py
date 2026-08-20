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
        "int_col": DataType.NUMBER,
        "float_col": DataType.NUMBER,
        "trig_col": DataType.NUMBER,
    }

    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            "abs(int_col)",
            "round(float_col)",
            "ceil(float_col)",
            "floor(float_col)",
            "sqrt(trig_col)",
            "exp(trig_col)",
            "sin(trig_col)",
            "cos(trig_col)",
            "tan(trig_col)",
            "cot(trig_col)",
        ]

    @classmethod
    def get_expression_input_data(cls) -> pl.DataFrame:
        df = pl.DataFrame(
            {
                "int_col": [-1, 1, -2, 2],
                "float_col": [1.1, 1.5, 2.1, 2.9],
                "trig_col": [0, 1, 2, 3],
                "cot_col": [0, 1, 2, 3],
            }
        )
        return df

    @classmethod
    def get_expected_df_from_input(
        cls, expression_input_data: pl.DataFrame, dialect: Dialect
    ) -> pl.DataFrame:
        """Get the expected results dataframe (computed in polars).

        Args:
            expression_input_data: The input data for the expressions
            dialect: The SQL dialect being tested

        Returns:
            pl.DataFrame: The expected results for validation
        """
        df = expression_input_data
        expected_df = pl.DataFrame(
            {
                "row": [0, 1, 2, 3],
                "col1": df["int_col"].abs(),
                "col2": df["float_col"].round(),
                "col3": df["float_col"].ceil(),
                "col4": df["float_col"].floor(),
                "col5": df["trig_col"].cast(pl.Float64).sqrt(),
                "col6": df["trig_col"].cast(pl.Float64).exp(),
                "col7": df["trig_col"].cast(pl.Float64).sin(),
                "col8": df["trig_col"].cast(pl.Float64).cos(),
                "col9": df["trig_col"].cast(pl.Float64).tan(),
                "col10": df.select(
                    pl.when(df["cot_col"] == 0)
                    .then(None)
                    .otherwise(1 / df["cot_col"].cast(pl.Float64).tan())
                ),
            }
        )
        return expected_df

    @classmethod
    def validate(
        cls, expected_df: pl.DataFrame, result_df: pl.DataFrame, dialect: Dialect
    ) -> None:
        """Validate the query results against expected values."""
        assert result_df.shape == (4, 11)
        pl_testing.assert_frame_equal(
            result_df, expected_df, check_dtypes=False, abs_tol=1e-6
        )


# Database result tests


def test_snapshot_math_functions_validate(dialect_name):
    """Test math functions expressions for each dialect separately."""
    dialect = Dialect.from_name(dialect_name)
    result_df = SnapshotTest.get_result_df(dialect)
    expected_df = SnapshotTest.get_expected_df(dialect)
    SnapshotTest.validate(expected_df, result_df, dialect)


@pytest.mark.database
@pytest.mark.database_local
def test_snapshot_math_functions_result():
    """Test math functions expressions for each dialect separately."""
    dialect_name = SnapshotTest.result_dialect
    dialect = Dialect.from_name(dialect_name)
    result_str = SnapshotTest.get_result_df_str(dialect)

    assert result_str == snapshot("""\
shape: (4, 11)
┌─────┬──────┬──────────────┬──────┬──────┬──────────┬───────────┬──────────┬───────────┬───────────┬───────────┐
│ row ┆ col1 ┆ col2         ┆ col3 ┆ col4 ┆ col5     ┆ col6      ┆ col7     ┆ col8      ┆ col9      ┆ col10     │
│ --- ┆ ---  ┆ ---          ┆ ---  ┆ ---  ┆ ---      ┆ ---       ┆ ---      ┆ ---       ┆ ---       ┆ ---       │
│ i32 ┆ i32  ┆ decimal[2,0] ┆ f64  ┆ f64  ┆ f64      ┆ f64       ┆ f64      ┆ f64       ┆ f64       ┆ f64       │
╞═════╪══════╪══════════════╪══════╪══════╪══════════╪═══════════╪══════════╪═══════════╪═══════════╪═══════════╡
│ 0   ┆ 1    ┆ 1            ┆ 2.0  ┆ 1.0  ┆ 0.0      ┆ 1.0       ┆ 0.0      ┆ 1.0       ┆ 0.0       ┆ null      │
│ 1   ┆ 1    ┆ 2            ┆ 2.0  ┆ 1.0  ┆ 1.0      ┆ 2.718282  ┆ 0.841471 ┆ 0.540302  ┆ 1.557408  ┆ 0.642093  │
│ 2   ┆ 2    ┆ 2            ┆ 3.0  ┆ 2.0  ┆ 1.414214 ┆ 7.389056  ┆ 0.909297 ┆ -0.416147 ┆ -2.18504  ┆ -0.457658 │
│ 3   ┆ 2    ┆ 3            ┆ 3.0  ┆ 2.0  ┆ 1.732051 ┆ 20.085537 ┆ 0.14112  ┆ -0.989992 ┆ -0.142547 ┆ -7.015253 │
└─────┴──────┴──────────────┴──────┴──────┴──────────┴───────────┴──────────┴───────────┴───────────┴───────────┘\
""")


# SQL expression snapshots


def test_snapshot_math_functions_sql():
    """Snapshot directly compiled calc SQL for every supported dialect."""
    assert SnapshotTest.render_sql_snapshot() == snapshot("""\
-- === BIGQUERY ===
ABS(`int_col`);
ROUND(`float_col`);
CEIL(CAST(`float_col` AS FLOAT64));
FLOOR(CAST(`float_col` AS FLOAT64));
SQRT(CAST(`trig_col` AS FLOAT64));
EXP(CAST(`trig_col` AS FLOAT64));
SIN(CAST(`trig_col` AS FLOAT64));
COS(CAST(`trig_col` AS FLOAT64));
TAN(CAST(`trig_col` AS FLOAT64));
CASE WHEN `trig_col` = 0 THEN NULL ELSE COT(CAST(`trig_col` AS FLOAT64)) END;

-- === CLICKHOUSE ===
ABS("int_col");
ROUND("float_col");
CEIL(CAST("float_col" AS Nullable(Float64)));
FLOOR(CAST("float_col" AS Nullable(Float64)));
SQRT(CAST("trig_col" AS Nullable(Float64)));
EXP(CAST("trig_col" AS Nullable(Float64)));
SIN(CAST("trig_col" AS Nullable(Float64)));
COS(CAST("trig_col" AS Nullable(Float64)));
TAN(CAST("trig_col" AS Nullable(Float64)));
CASE
  WHEN "trig_col" = 0
  THEN NULL
  ELSE 1.0 / TAN(CAST("trig_col" AS Nullable(Float64)))
END;

-- === DUCKDB ===
ABS("int_col");
ROUND("float_col");
CEIL(CAST("float_col" AS DOUBLE));
FLOOR(CAST("float_col" AS DOUBLE));
SQRT(CAST("trig_col" AS DOUBLE));
EXP(CAST("trig_col" AS DOUBLE));
SIN(CAST("trig_col" AS DOUBLE));
COS(CAST("trig_col" AS DOUBLE));
TAN(CAST("trig_col" AS DOUBLE));
CASE WHEN "trig_col" = 0 THEN NULL ELSE COT(CAST("trig_col" AS DOUBLE)) END;

-- === MSSQL ===
ABS([int_col]);
ROUND([float_col], 0);
CEILING(CAST([float_col] AS FLOAT));
FLOOR(CAST([float_col] AS FLOAT));
SQRT(CAST([trig_col] AS FLOAT));
EXP(CAST([trig_col] AS FLOAT));
SIN(CAST([trig_col] AS FLOAT));
COS(CAST([trig_col] AS FLOAT));
TAN(CAST([trig_col] AS FLOAT));
CASE
  WHEN [trig_col] = 0
  THEN NULL
  ELSE CAST(1.0 AS FLOAT) / TAN(CAST([trig_col] AS FLOAT))
END;

-- === MYSQL ===
ABS(`int_col`);
ROUND(`float_col`);
CEIL(CAST(`float_col` AS DOUBLE));
FLOOR(CAST(`float_col` AS DOUBLE));
SQRT(CAST(`trig_col` AS DOUBLE));
EXP(CAST(`trig_col` AS DOUBLE));
SIN(CAST(`trig_col` AS DOUBLE));
COS(CAST(`trig_col` AS DOUBLE));
TAN(CAST(`trig_col` AS DOUBLE));
CASE WHEN `trig_col` = 0 THEN NULL ELSE COT(CAST(`trig_col` AS DOUBLE)) END;

-- === POSTGRES ===
ABS("int_col");
ROUND("float_col");
CEIL(CAST("float_col" AS DOUBLE PRECISION));
FLOOR(CAST("float_col" AS DOUBLE PRECISION));
SQRT(CAST("trig_col" AS DOUBLE PRECISION));
EXP(CAST("trig_col" AS DOUBLE PRECISION));
SIN(CAST("trig_col" AS DOUBLE PRECISION));
COS(CAST("trig_col" AS DOUBLE PRECISION));
TAN(CAST("trig_col" AS DOUBLE PRECISION));
CASE
  WHEN "trig_col" = 0
  THEN NULL
  ELSE COT(CAST("trig_col" AS DOUBLE PRECISION))
END;

-- === REDSHIFT ===
ABS("int_col");
ROUND("float_col");
CEIL(CAST("float_col" AS DOUBLE PRECISION));
FLOOR(CAST("float_col" AS DOUBLE PRECISION));
SQRT(CAST("trig_col" AS DOUBLE PRECISION));
EXP(CAST("trig_col" AS DOUBLE PRECISION));
SIN(CAST("trig_col" AS DOUBLE PRECISION));
COS(CAST("trig_col" AS DOUBLE PRECISION));
TAN(CAST("trig_col" AS DOUBLE PRECISION));
CASE
  WHEN "trig_col" = 0
  THEN NULL
  ELSE COT(CAST("trig_col" AS DOUBLE PRECISION))
END;

-- === SNOWFLAKE ===
ABS("int_col");
ROUND("float_col");
CEIL(CAST("float_col" AS DOUBLE));
FLOOR(CAST("float_col" AS DOUBLE));
SQRT(CAST("trig_col" AS DOUBLE));
EXP(CAST("trig_col" AS DOUBLE));
SIN(CAST("trig_col" AS DOUBLE));
COS(CAST("trig_col" AS DOUBLE));
TAN(CAST("trig_col" AS DOUBLE));
CASE WHEN "trig_col" = 0 THEN NULL ELSE COT(CAST("trig_col" AS DOUBLE)) END;

-- === SPARK ===
ABS(`int_col`);
ROUND(`float_col`);
CEIL(CAST(`float_col` AS DOUBLE));
FLOOR(CAST(`float_col` AS DOUBLE));
SQRT(CAST(`trig_col` AS DOUBLE));
EXP(CAST(`trig_col` AS DOUBLE));
SIN(CAST(`trig_col` AS DOUBLE));
COS(CAST(`trig_col` AS DOUBLE));
TAN(CAST(`trig_col` AS DOUBLE));
CASE WHEN `trig_col` = 0 THEN NULL ELSE COT(CAST(`trig_col` AS DOUBLE)) END;

-- === TRINO ===
ABS("int_col");
ROUND("float_col");
CEIL(CAST("float_col" AS DOUBLE));
FLOOR(CAST("float_col" AS DOUBLE));
SQRT(CAST("trig_col" AS DOUBLE));
EXP(CAST("trig_col" AS DOUBLE));
SIN(CAST("trig_col" AS DOUBLE));
COS(CAST("trig_col" AS DOUBLE));
TAN(CAST("trig_col" AS DOUBLE));
CASE
  WHEN "trig_col" = 0
  THEN NULL
  ELSE CAST(1.0 AS DOUBLE) / TAN(CAST("trig_col" AS DOUBLE))
END;
""")
