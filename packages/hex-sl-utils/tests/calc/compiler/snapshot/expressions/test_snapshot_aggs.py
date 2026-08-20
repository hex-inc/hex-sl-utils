from __future__ import annotations

import polars as pl
import pytest
from inline_snapshot import snapshot

from hex_sl_utils.datatype import DataType
from hex_sl_utils.dialect import Dialect

from ..snapshot_base import AggregationSnapshotTestBase


class SnapshotTest(AggregationSnapshotTestBase):
    columns = {
        "numeric_col": DataType.NUMBER,
        "var_col": DataType.NUMBER,
        "boolean_col": DataType.BOOLEAN,
        "boolean_num_col": DataType.NUMBER,
        "null_col": DataType.NUMBER,
    }

    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            "min(numeric_col)",
            "max(numeric_col)",
            "sum(numeric_col)",
            "mean(numeric_col)",
            "stddev(numeric_col)",
            "stddevpop(numeric_col)",
            "variance(var_col)",
            "variancepop(var_col)",
            "count()",
            "count(null_col)",
            "countdistinct(null_col)",
            "sumboolean(boolean_col)",
            "sumboolean(boolean_num_col)",
        ]

    @classmethod
    def get_expression_input_data(cls) -> pl.DataFrame:
        df = pl.DataFrame(
            {
                "numeric_col": [-1, 1, -2, 2],
                "var_col": [1, 1, 1, 7],
                "boolean_col": [True, False, True, None],
                "boolean_num_col": [1, 0, 2, None],
                "null_col": [-1.0, None, -2.0, float("nan")],
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
                "col1": [df["numeric_col"].min()],
                "col2": [df["numeric_col"].max()],
                "col3": [df["numeric_col"].sum()],
                "col4": [df["numeric_col"].mean()],
                "col5": [df["numeric_col"].std(ddof=1)],
                "col6": [df["numeric_col"].std(ddof=0)],
                "col7": [df["var_col"].var(ddof=1)],
                "col8": [df["var_col"].var(ddof=0)],
                "col9": [len(df)],
                "col10": [
                    df["null_col"].count()
                    if dialect.supports_non_finite_floats()
                    # If nan's aren't support these are treated as NULL by the dialect
                    else df["null_col"].drop_nans().count()
                ],
                "col11": [
                    df["null_col"].drop_nulls().n_unique()
                    if dialect.supports_non_finite_floats()
                    # If nan's aren't support these are treated as NULL by the dialect
                    else df["null_col"].drop_nulls().drop_nans().n_unique()
                ],
                "col12": [df["boolean_col"].sum()],
                "col13": [df["boolean_num_col"].cast(pl.Boolean).cast(pl.Int32).sum()],
            }
        )
        return expected_df


# Database result tests


def test_snapshot_aggs_validate(dialect_name):
    """Test aggregate expressions for each dialect separately."""
    dialect = Dialect.from_name(dialect_name)
    result_df = SnapshotTest.get_result_df(dialect)
    expected_df = SnapshotTest.get_expected_df(dialect)
    SnapshotTest.validate(expected_df, result_df, dialect)


@pytest.mark.database
@pytest.mark.database_local
def test_snapshot_aggs_result():
    """Test aggregate expression results in DuckDB."""
    dialect = Dialect.from_name(SnapshotTest.result_dialect)
    result_str = SnapshotTest.get_result_df_str(dialect)

    assert result_str == snapshot("""\
shape: (1, 13)
┌──────┬──────┬───────────────┬──────┬──────────┬──────────┬──────┬──────┬──────┬───────┬───────┬───────────────┬───────────────┐
│ col1 ┆ col2 ┆ col3          ┆ col4 ┆ col5     ┆ col6     ┆ col7 ┆ col8 ┆ col9 ┆ col10 ┆ col11 ┆ col12         ┆ col13         │
│ ---  ┆ ---  ┆ ---           ┆ ---  ┆ ---      ┆ ---      ┆ ---  ┆ ---  ┆ ---  ┆ ---   ┆ ---   ┆ ---           ┆ ---           │
│ i32  ┆ i32  ┆ decimal[38,0] ┆ f64  ┆ f64      ┆ f64      ┆ f64  ┆ f64  ┆ i64  ┆ i64   ┆ i64   ┆ decimal[38,0] ┆ decimal[38,0] │
╞══════╪══════╪═══════════════╪══════╪══════════╪══════════╪══════╪══════╪══════╪═══════╪═══════╪═══════════════╪═══════════════╡
│ -2   ┆ 2    ┆ 0             ┆ 0.0  ┆ 1.825742 ┆ 1.581139 ┆ 9.0  ┆ 6.75 ┆ 4    ┆ 3     ┆ 3     ┆ 2             ┆ 2             │
└──────┴──────┴───────────────┴──────┴──────────┴──────────┴──────┴──────┴──────┴───────┴───────┴───────────────┴───────────────┘\
""")
