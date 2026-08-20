from __future__ import annotations

import polars as pl
import pytest
from inline_snapshot import snapshot

from hex_sl_utils.datatype import DataType
from hex_sl_utils.dialect import Dialect

from ..snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    columns = {
        "lhs": DataType.NUMBER,
        "rhs": DataType.NUMBER,
        "nullable": DataType.NUMBER,
        "switch_input": DataType.NUMBER,
    }

    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            "if(lhs > 0, lhs, -100)",
            "isnull(nullable)",
            "isoneof(lhs, 1, 2, 3)",
            # Testing isfinite on only finite values here so that we test all
            # dialects, even those that don't support non-finite values.
            # The behavior for dialects that do support non-finite values
            # is tested in test_snapshot_isfinite.py
            "isfinite(lhs)",
            # Switch function without default
            "switch(switch_input, 1, 'A', 2, 'B', 3, 'C')",
            # Switch function with default
            "switch(switch_input, 1, 'A', 2, 'B', 3, 'C', 'Other')",
        ]

    @classmethod
    def get_expression_input_data(cls) -> pl.DataFrame:
        return pl.DataFrame(
            {
                "lhs": [-1, 10, -2, 2],
                "rhs": [2, 2, -12, 2],
                "nullable": [None, 10, -2, 2],
                "switch_input": [1, 2, 3, 4],
            }
        )

    @classmethod
    def get_expected_df_from_input(
        cls, expression_input_data: pl.DataFrame, dialect: Dialect
    ) -> pl.DataFrame:
        df = expression_input_data
        expected_df = pl.DataFrame(
            {
                "row": [0, 1, 2, 3],
                "col1": df.select(
                    pl.when(df["lhs"] > 0).then(df["lhs"]).otherwise(-100)
                ),
                "col2": df["nullable"].is_null(),
                "col3": df["lhs"].is_in([1, 2, 3]),
                "col4": df["lhs"].is_finite(),
                "col5": df.select(
                    pl.when(df["switch_input"] == 1)
                    .then(pl.lit("A"))
                    .when(df["switch_input"] == 2)
                    .then(pl.lit("B"))
                    .when(df["switch_input"] == 3)
                    .then(pl.lit("C"))
                    .otherwise(None)
                ),
                "col6": df.select(
                    pl.when(df["switch_input"] == 1)
                    .then(pl.lit("A"))
                    .when(df["switch_input"] == 2)
                    .then(pl.lit("B"))
                    .when(df["switch_input"] == 3)
                    .then(pl.lit("C"))
                    .otherwise(pl.lit("Other"))
                ),
            }
        )
        return expected_df


# Database result tests


def test_snapshot_control_functions_validate(dialect_name):
    """Test control flow validation for each dialect."""
    dialect = Dialect.from_name(dialect_name)
    result_df = SnapshotTest.get_result_df(dialect)
    expected_df = SnapshotTest.get_expected_df(dialect)
    SnapshotTest.validate(expected_df, result_df, dialect)


@pytest.mark.database
@pytest.mark.database_local
def test_snapshot_control_functions_result():
    """Test control flow result output."""
    dialect = Dialect.from_name(SnapshotTest.result_dialect)
    result_str = SnapshotTest.get_result_df_str(dialect)

    assert result_str == snapshot("""\
shape: (4, 7)
┌─────┬──────┬───────┬───────┬──────┬──────┬───────┐
│ row ┆ col1 ┆ col2  ┆ col3  ┆ col4 ┆ col5 ┆ col6  │
│ --- ┆ ---  ┆ ---   ┆ ---   ┆ ---  ┆ ---  ┆ ---   │
│ i32 ┆ i32  ┆ bool  ┆ bool  ┆ bool ┆ str  ┆ str   │
╞═════╪══════╪═══════╪═══════╪══════╪══════╪═══════╡
│ 0   ┆ -100 ┆ true  ┆ false ┆ true ┆ A    ┆ A     │
│ 1   ┆ 10   ┆ false ┆ false ┆ true ┆ B    ┆ B     │
│ 2   ┆ -100 ┆ false ┆ false ┆ true ┆ C    ┆ C     │
│ 3   ┆ 2    ┆ false ┆ true  ┆ true ┆ null ┆ Other │
└─────┴──────┴───────┴───────┴──────┴──────┴───────┘\
""")


# SQL expression snapshots


def test_snapshot_control_functions_sql():
    """Snapshot directly compiled calc SQL for every supported dialect."""
    assert SnapshotTest.render_sql_snapshot() == snapshot("""\
-- === BIGQUERY ===
CASE WHEN `lhs` > 0 THEN `lhs` ELSE -100 END;
`nullable` IS NULL;
`lhs` IN (1, 2, 3);
NOT (
  `lhs` IS NULL
  OR IS_NAN(CAST(`lhs` AS FLOAT64))
  OR `lhs` = CAST('Infinity' AS FLOAT64)
  OR `lhs` = CAST('-Infinity' AS FLOAT64)
);
CASE
  WHEN `switch_input` = 1
  THEN 'A'
  WHEN `switch_input` = 2
  THEN 'B'
  WHEN `switch_input` = 3
  THEN 'C'
END;
CASE
  WHEN `switch_input` = 1
  THEN 'A'
  WHEN `switch_input` = 2
  THEN 'B'
  WHEN `switch_input` = 3
  THEN 'C'
  ELSE 'Other'
END;

-- === CLICKHOUSE ===
CASE WHEN "lhs" > 0 THEN "lhs" ELSE -100 END;
"nullable" IS NULL;
"lhs" IN (1, 2, 3);
NOT (
  "lhs" IS NULL
  OR isNaN(CAST("lhs" AS Nullable(Float64)))
  OR "lhs" = CAST('Infinity' AS Nullable(Float64))
  OR "lhs" = CAST('-Infinity' AS Nullable(Float64))
);
CASE
  WHEN "switch_input" = 1
  THEN 'A'
  WHEN "switch_input" = 2
  THEN 'B'
  WHEN "switch_input" = 3
  THEN 'C'
END;
CASE
  WHEN "switch_input" = 1
  THEN 'A'
  WHEN "switch_input" = 2
  THEN 'B'
  WHEN "switch_input" = 3
  THEN 'C'
  ELSE 'Other'
END;

-- === DUCKDB ===
CASE WHEN "lhs" > 0 THEN "lhs" ELSE -100 END;
"nullable" IS NULL;
"lhs" IN (1, 2, 3);
NOT (
  "lhs" IS NULL OR ISNAN("lhs") OR ISINF("lhs")
);
CASE
  WHEN "switch_input" = 1
  THEN 'A'
  WHEN "switch_input" = 2
  THEN 'B'
  WHEN "switch_input" = 3
  THEN 'C'
END;
CASE
  WHEN "switch_input" = 1
  THEN 'A'
  WHEN "switch_input" = 2
  THEN 'B'
  WHEN "switch_input" = 3
  THEN 'C'
  ELSE 'Other'
END;

-- === MSSQL ===
CASE WHEN [lhs] > 0 THEN [lhs] ELSE -100 END;
IIF([nullable] IS NULL, 1, 0);
IIF([lhs] IN (1, 2, 3), 1, 0);
IIF(NOT [lhs] IS NULL, 1, 0);
CASE
  WHEN [switch_input] = 1
  THEN 'A'
  WHEN [switch_input] = 2
  THEN 'B'
  WHEN [switch_input] = 3
  THEN 'C'
END;
CASE
  WHEN [switch_input] = 1
  THEN 'A'
  WHEN [switch_input] = 2
  THEN 'B'
  WHEN [switch_input] = 3
  THEN 'C'
  ELSE 'Other'
END;

-- === MYSQL ===
CASE WHEN `lhs` > 0 THEN `lhs` ELSE -100 END;
`nullable` IS NULL;
`lhs` IN (1, 2, 3);
NOT `lhs` IS NULL;
CASE
  WHEN `switch_input` = 1
  THEN 'A'
  WHEN `switch_input` = 2
  THEN 'B'
  WHEN `switch_input` = 3
  THEN 'C'
END;
CASE
  WHEN `switch_input` = 1
  THEN 'A'
  WHEN `switch_input` = 2
  THEN 'B'
  WHEN `switch_input` = 3
  THEN 'C'
  ELSE 'Other'
END;

-- === POSTGRES ===
CASE WHEN "lhs" > 0 THEN "lhs" ELSE -100 END;
"nullable" IS NULL;
"lhs" IN (1, 2, 3);
NOT (
  "lhs" IS NULL
  OR CAST("lhs" AS DOUBLE PRECISION) = CAST('NaN' AS DOUBLE PRECISION)
  OR "lhs" = CAST('Infinity' AS DOUBLE PRECISION)
  OR "lhs" = CAST('-Infinity' AS DOUBLE PRECISION)
);
CASE
  WHEN "switch_input" = 1
  THEN 'A'
  WHEN "switch_input" = 2
  THEN 'B'
  WHEN "switch_input" = 3
  THEN 'C'
END;
CASE
  WHEN "switch_input" = 1
  THEN 'A'
  WHEN "switch_input" = 2
  THEN 'B'
  WHEN "switch_input" = 3
  THEN 'C'
  ELSE 'Other'
END;

-- === REDSHIFT ===
CASE WHEN "lhs" > 0 THEN "lhs" ELSE -100 END;
"nullable" IS NULL;
"lhs" IN (1, 2, 3);
NOT (
  "lhs" IS NULL
  OR CAST("lhs" AS DOUBLE PRECISION) = CAST('NaN' AS DOUBLE PRECISION)
  OR "lhs" = CAST('Infinity' AS DOUBLE PRECISION)
  OR "lhs" = CAST('-Infinity' AS DOUBLE PRECISION)
);
CASE
  WHEN "switch_input" = 1
  THEN CAST('A' AS VARCHAR(MAX))
  WHEN "switch_input" = 2
  THEN CAST('B' AS VARCHAR(MAX))
  WHEN "switch_input" = 3
  THEN CAST('C' AS VARCHAR(MAX))
END;
CASE
  WHEN "switch_input" = 1
  THEN CAST('A' AS VARCHAR(MAX))
  WHEN "switch_input" = 2
  THEN CAST('B' AS VARCHAR(MAX))
  WHEN "switch_input" = 3
  THEN CAST('C' AS VARCHAR(MAX))
  ELSE CAST('Other' AS VARCHAR(MAX))
END;

-- === SNOWFLAKE ===
CASE WHEN "lhs" > 0 THEN "lhs" ELSE -100 END;
"nullable" IS NULL;
"lhs" IN (1, 2, 3);
NOT (
  "lhs" IS NULL
  OR CAST("lhs" AS DOUBLE) = CAST('NaN' AS DOUBLE)
  OR "lhs" = CAST('Infinity' AS DOUBLE)
  OR "lhs" = CAST('-Infinity' AS DOUBLE)
);
CASE
  WHEN "switch_input" = 1
  THEN 'A'
  WHEN "switch_input" = 2
  THEN 'B'
  WHEN "switch_input" = 3
  THEN 'C'
END;
CASE
  WHEN "switch_input" = 1
  THEN 'A'
  WHEN "switch_input" = 2
  THEN 'B'
  WHEN "switch_input" = 3
  THEN 'C'
  ELSE 'Other'
END;

-- === SPARK ===
CASE WHEN `lhs` > 0 THEN `lhs` ELSE -100 END;
`nullable` IS NULL;
`lhs` IN (1, 2, 3);
NOT (
  `lhs` IS NULL
  OR ISNAN(CAST(`lhs` AS DOUBLE))
  OR `lhs` = CAST('Infinity' AS DOUBLE)
  OR `lhs` = CAST('-Infinity' AS DOUBLE)
);
CASE
  WHEN `switch_input` = 1
  THEN 'A'
  WHEN `switch_input` = 2
  THEN 'B'
  WHEN `switch_input` = 3
  THEN 'C'
END;
CASE
  WHEN `switch_input` = 1
  THEN 'A'
  WHEN `switch_input` = 2
  THEN 'B'
  WHEN `switch_input` = 3
  THEN 'C'
  ELSE 'Other'
END;

-- === TRINO ===
CASE WHEN "lhs" > 0 THEN "lhs" ELSE -100 END;
"nullable" IS NULL;
"lhs" IN (1, 2, 3);
NOT (
  "lhs" IS NULL
  OR IS_NAN(CAST("lhs" AS DOUBLE))
  OR "lhs" = CAST('Infinity' AS DOUBLE)
  OR "lhs" = CAST('-Infinity' AS DOUBLE)
);
CASE
  WHEN "switch_input" = 1
  THEN 'A'
  WHEN "switch_input" = 2
  THEN 'B'
  WHEN "switch_input" = 3
  THEN 'C'
END;
CASE
  WHEN "switch_input" = 1
  THEN 'A'
  WHEN "switch_input" = 2
  THEN 'B'
  WHEN "switch_input" = 3
  THEN 'C'
  ELSE 'Other'
END;
""")
