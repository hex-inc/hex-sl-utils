from __future__ import annotations

import polars as pl
import pytest
from inline_snapshot import snapshot

from hex_sl_utils.datatype import DataType
from hex_sl_utils.dialect import Dialect

from ..snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    columns = {
        "numeric_col": DataType.NUMBER,
        "var_col": DataType.NUMBER,
        "null_col": DataType.NUMBER,
    }

    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            "max(numeric_col)",
            "sum(numeric_col)",
            "mean(numeric_col)",
            "stddev(numeric_col)",
            "variance(var_col)",
            "variancepop(var_col)",
            "count()",
            "count(null_col)",
        ]

    @classmethod
    def get_expression_input_data(cls) -> pl.DataFrame:
        df = pl.DataFrame(
            {
                "numeric_col": [-1, 1, -2, 2],
                "var_col": [1, 1, 1, 7],
                "null_col": [-1, None, -2, 2],
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
                "col1": [df["numeric_col"].max()] * 4,
                "col2": [df["numeric_col"].sum()] * 4,
                "col3": [df["numeric_col"].mean()] * 4,
                "col4": [df["numeric_col"].std(ddof=1)] * 4,
                "col5": [df["var_col"].var(ddof=1)] * 4,
                "col6": [df["var_col"].var(ddof=0)] * 4,
                "col7": [len(df)] * 4,
                "col8": [df["null_col"].count()] * 4,
            }
        )
        return expected_df


# Database result tests


def test_snapshot_window_aggs_validate(dialect_name):
    """Test window aggregate expressions for each dialect separately."""
    dialect = Dialect.from_name(dialect_name)
    result_df = SnapshotTest.get_result_df(dialect)
    expected_df = SnapshotTest.get_expected_df(dialect)
    SnapshotTest.validate(expected_df, result_df, dialect)


@pytest.mark.database
@pytest.mark.database_local
def test_snapshot_window_aggs_result():
    """Test window aggregate expressions for each dialect separately."""
    dialect_name = SnapshotTest.result_dialect
    dialect = Dialect.from_name(dialect_name)
    result_str = SnapshotTest.get_result_df_str(dialect)

    assert result_str == snapshot("""\
shape: (4, 9)
┌─────┬──────┬───────────────┬──────┬──────────┬──────┬──────┬──────┬──────┐
│ row ┆ col1 ┆ col2          ┆ col3 ┆ col4     ┆ col5 ┆ col6 ┆ col7 ┆ col8 │
│ --- ┆ ---  ┆ ---           ┆ ---  ┆ ---      ┆ ---  ┆ ---  ┆ ---  ┆ ---  │
│ i32 ┆ i32  ┆ decimal[38,0] ┆ f64  ┆ f64      ┆ f64  ┆ f64  ┆ i64  ┆ i64  │
╞═════╪══════╪═══════════════╪══════╪══════════╪══════╪══════╪══════╪══════╡
│ 0   ┆ 2    ┆ 0             ┆ 0.0  ┆ 1.825742 ┆ 9.0  ┆ 6.75 ┆ 4    ┆ 3    │
│ 1   ┆ 2    ┆ 0             ┆ 0.0  ┆ 1.825742 ┆ 9.0  ┆ 6.75 ┆ 4    ┆ 3    │
│ 2   ┆ 2    ┆ 0             ┆ 0.0  ┆ 1.825742 ┆ 9.0  ┆ 6.75 ┆ 4    ┆ 3    │
│ 3   ┆ 2    ┆ 0             ┆ 0.0  ┆ 1.825742 ┆ 9.0  ┆ 6.75 ┆ 4    ┆ 3    │
└─────┴──────┴───────────────┴──────┴──────────┴──────┴──────┴──────┴──────┘\
""")


# SQL expression snapshots


def test_snapshot_window_aggs_sql():
    """Snapshot directly compiled calc SQL for every supported dialect."""
    assert SnapshotTest.render_sql_snapshot() == snapshot("""\
-- === BIGQUERY ===
MAX(`numeric_col`) OVER ();
SUM(`numeric_col`) OVER ();
AVG(CAST(`numeric_col` AS FLOAT64)) OVER ();
STDDEV_SAMP(CAST(`numeric_col` AS FLOAT64)) OVER ();
VARIANCE(CAST(`var_col` AS FLOAT64)) OVER ();
VAR_POP(CAST(`var_col` AS FLOAT64)) OVER ();
COUNT(1) OVER ();
COUNT(`null_col`) OVER ();

-- === CLICKHOUSE ===
MAX("numeric_col") OVER ();
SUM("numeric_col") OVER ();
AVG(CAST("numeric_col" AS Nullable(Float64))) OVER ();
STDDEV_SAMP(CAST("numeric_col" AS Nullable(Float64))) OVER ();
varSamp(CAST("var_col" AS Nullable(Float64))) OVER ();
varPop(CAST("var_col" AS Nullable(Float64))) OVER ();
COUNT(1) OVER ();
COUNT("null_col") OVER ();

-- === DUCKDB ===
MAX("numeric_col") OVER ();
SUM("numeric_col") OVER ();
AVG(CAST("numeric_col" AS DOUBLE)) OVER ();
STDDEV_SAMP(CAST("numeric_col" AS DOUBLE)) OVER ();
VARIANCE(CAST("var_col" AS DOUBLE)) OVER ();
VAR_POP(CAST("var_col" AS DOUBLE)) OVER ();
COUNT(1) OVER ();
COUNT("null_col") OVER ();

-- === MSSQL ===
MAX([numeric_col]) OVER ();
SUM([numeric_col]) OVER ();
AVG(CAST([numeric_col] AS FLOAT)) OVER ();
STDEV(CAST([numeric_col] AS FLOAT)) OVER ();
VAR(CAST([var_col] AS FLOAT)) OVER ();
VARP(CAST([var_col] AS FLOAT)) OVER ();
COUNT(*) OVER ();
COUNT([null_col]) OVER ();

-- === MYSQL ===
MAX(`numeric_col`) OVER ();
SUM(`numeric_col`) OVER ();
AVG(CAST(`numeric_col` AS DOUBLE)) OVER ();
STDDEV_SAMP(CAST(`numeric_col` AS DOUBLE)) OVER ();
VAR_SAMP(CAST(`var_col` AS DOUBLE)) OVER ();
VAR_POP(CAST(`var_col` AS DOUBLE)) OVER ();
COUNT(1) OVER ();
COUNT(`null_col`) OVER ();

-- === POSTGRES ===
MAX("numeric_col") OVER ();
SUM("numeric_col") OVER ();
AVG(CAST("numeric_col" AS DOUBLE PRECISION)) OVER ();
STDDEV_SAMP(CAST("numeric_col" AS DOUBLE PRECISION)) OVER ();
VAR_SAMP(CAST("var_col" AS DOUBLE PRECISION)) OVER ();
VAR_POP(CAST("var_col" AS DOUBLE PRECISION)) OVER ();
COUNT(1) OVER ();
COUNT("null_col") OVER ();

-- === REDSHIFT ===
MAX("numeric_col") OVER ();
SUM("numeric_col") OVER ();
AVG(CAST("numeric_col" AS DOUBLE PRECISION)) OVER ();
STDDEV_SAMP(CAST("numeric_col" AS DOUBLE PRECISION)) OVER ();
VAR_SAMP(CAST("var_col" AS DOUBLE PRECISION)) OVER ();
VAR_POP(CAST("var_col" AS DOUBLE PRECISION)) OVER ();
COUNT(1) OVER ();
COUNT("null_col") OVER ();

-- === SNOWFLAKE ===
MAX("numeric_col") OVER ();
SUM("numeric_col") OVER ();
AVG(CAST("numeric_col" AS DOUBLE)) OVER ();
STDDEV_SAMP(CAST("numeric_col" AS DOUBLE)) OVER ();
VARIANCE(CAST("var_col" AS DOUBLE)) OVER ();
VARIANCE_POP(CAST("var_col" AS DOUBLE)) OVER ();
COUNT(1) OVER ();
COUNT("null_col") OVER ();

-- === SPARK ===
MAX(`numeric_col`) OVER ();
SUM(`numeric_col`) OVER ();
AVG(CAST(`numeric_col` AS DOUBLE)) OVER ();
STDDEV_SAMP(CAST(`numeric_col` AS DOUBLE)) OVER ();
VARIANCE(CAST(`var_col` AS DOUBLE)) OVER ();
VAR_POP(CAST(`var_col` AS DOUBLE)) OVER ();
COUNT(1) OVER ();
COUNT(`null_col`) OVER ();

-- === TRINO ===
MAX("numeric_col") OVER ();
SUM("numeric_col") OVER ();
AVG(CAST("numeric_col" AS DOUBLE)) OVER ();
STDDEV_SAMP(CAST("numeric_col" AS DOUBLE)) OVER ();
VARIANCE(CAST("var_col" AS DOUBLE)) OVER ();
VAR_POP(CAST("var_col" AS DOUBLE)) OVER ();
COUNT(1) OVER ();
COUNT("null_col") OVER ();
""")
