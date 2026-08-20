from __future__ import annotations

from datetime import datetime

import polars as pl
import polars.testing as pl_testing
import pytest
from inline_snapshot import snapshot

from hex_sl_utils.datatype import DataType
from hex_sl_utils.dialect import Dialect

from ..snapshot_base import SelectionSnapshotTestBase


class SnapshotTest(SelectionSnapshotTestBase):
    columns = {
        "ts": DataType.TIMESTAMP,
    }

    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        return [
            "year(ts)",
            "quarter(ts)",
            "month(ts)",
            "day(ts)",
            "dayofweek(ts)",
            "hour(ts)",
            "minute(ts)",
            "second(ts)",
            "millisecond(ts)",
        ]

    @classmethod
    def get_expression_input_data(cls) -> pl.DataFrame:
        df = pl.DataFrame(
            {
                "ts": [
                    datetime(2021, 1, 1, 0, 0, 0, 123000),
                    datetime(2022, 5, 15, 14, 45, 30, 456000),
                    datetime(2023, 12, 30, 18, 20, 15, 789000),
                    datetime(2024, 9, 12, 23, 59, 59, 999000),
                ]
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
                "col1": df.select(pl.col("ts").dt.year()),
                "col2": df.select(pl.col("ts").dt.quarter()),
                "col3": df.select(pl.col("ts").dt.month()),
                "col4": df.select(pl.col("ts").dt.day()),
                "col5": df.select(pl.col("ts").dt.weekday() % 7 + 1),
                "col6": df.select(pl.col("ts").dt.hour()),
                "col7": df.select(pl.col("ts").dt.minute()),
                "col8": df.select(pl.col("ts").dt.second()),
                "col9": df.select(pl.col("ts").dt.millisecond()),
            }
        )
        return expected_df

    @classmethod
    def validate(
        cls, expected_df: pl.DataFrame, result_df: pl.DataFrame, dialect: Dialect
    ) -> None:
        """Validate the query results against expected values."""
        assert result_df.shape == (4, 10)
        pl_testing.assert_frame_equal(
            result_df, expected_df, check_dtypes=False, abs_tol=1e-6
        )


# Database result tests


def test_snapshot_datepart_ts_validate(dialect_name):
    """Test datepart timestamp expressions for each dialect separately."""
    dialect = Dialect.from_name(dialect_name)
    result_df = SnapshotTest.get_result_df(dialect)
    expected_df = SnapshotTest.get_expected_df(dialect)
    SnapshotTest.validate(expected_df, result_df, dialect)


@pytest.mark.database
@pytest.mark.database_local
def test_snapshot_datepart_ts_result():
    """Test datepart timestamp expressions for each dialect separately."""
    dialect_name = SnapshotTest.result_dialect
    dialect = Dialect.from_name(dialect_name)
    result_str = SnapshotTest.get_result_df_str(dialect)

    assert result_str == snapshot("""\
shape: (4, 10)
┌─────┬──────┬──────┬──────┬──────┬──────┬──────┬──────┬──────┬──────┐
│ row ┆ col1 ┆ col2 ┆ col3 ┆ col4 ┆ col5 ┆ col6 ┆ col7 ┆ col8 ┆ col9 │
│ --- ┆ ---  ┆ ---  ┆ ---  ┆ ---  ┆ ---  ┆ ---  ┆ ---  ┆ ---  ┆ ---  │
│ i32 ┆ i64  ┆ i64  ┆ i64  ┆ i64  ┆ i64  ┆ i64  ┆ i64  ┆ i64  ┆ i64  │
╞═════╪══════╪══════╪══════╪══════╪══════╪══════╪══════╪══════╪══════╡
│ 0   ┆ 2021 ┆ 1    ┆ 1    ┆ 1    ┆ 6    ┆ 0    ┆ 0    ┆ 0    ┆ 123  │
│ 1   ┆ 2022 ┆ 2    ┆ 5    ┆ 15   ┆ 1    ┆ 14   ┆ 45   ┆ 30   ┆ 456  │
│ 2   ┆ 2023 ┆ 4    ┆ 12   ┆ 30   ┆ 7    ┆ 18   ┆ 20   ┆ 15   ┆ 789  │
│ 3   ┆ 2024 ┆ 3    ┆ 9    ┆ 12   ┆ 5    ┆ 23   ┆ 59   ┆ 59   ┆ 999  │
└─────┴──────┴──────┴──────┴──────┴──────┴──────┴──────┴──────┴──────┘\
""")


# SQL expression snapshots


def test_snapshot_datepart_ts_sql():
    """Snapshot directly compiled calc SQL for every supported dialect."""
    assert SnapshotTest.render_sql_snapshot() == snapshot("""\
-- === BIGQUERY ===
EXTRACT(YEAR FROM `ts`);
EXTRACT(QUARTER FROM `ts`);
EXTRACT(MONTH FROM `ts`);
EXTRACT(DAY FROM `ts`);
EXTRACT(DAYOFWEEK FROM `ts`);
EXTRACT(HOUR FROM `ts`);
EXTRACT(MINUTE FROM `ts`);
CAST(TRUNC(EXTRACT(SECOND FROM `ts`)) AS INT64);
MOD(EXTRACT(MILLISECOND FROM `ts`), 1000);

-- === CLICKHOUSE ===
EXTRACT(YEAR FROM "ts");
EXTRACT(QUARTER FROM "ts");
EXTRACT(MONTH FROM "ts");
EXTRACT(DAY FROM "ts");
toDayOfWeek("ts", 3);
EXTRACT(HOUR FROM "ts");
EXTRACT(MINUTE FROM "ts");
CAST(EXTRACT(SECOND FROM "ts") AS Nullable(Int32));
EXTRACT(MILLISECOND FROM "ts") % 1000;

-- === DUCKDB ===
EXTRACT(YEAR FROM "ts");
EXTRACT(QUARTER FROM "ts");
EXTRACT(MONTH FROM "ts");
EXTRACT(DAY FROM "ts");
EXTRACT(DAYOFWEEK FROM "ts") + 1;
EXTRACT(HOUR FROM "ts");
EXTRACT(MINUTE FROM "ts");
CAST(EXTRACT(SECOND FROM "ts") AS BIGINT);
EXTRACT('MILLISECOND' FROM "ts") % 1000;

-- === MSSQL ===
DATEPART(YEAR, [ts]);
DATEPART(QUARTER, [ts]);
DATEPART(MONTH, [ts]);
DATEPART(DAY, [ts]);
DATEPART(DW, [ts]);
DATEPART(HOUR, [ts]);
DATEPART(MINUTE, [ts]);
CAST(DATEPART(SECOND, [ts]) AS INTEGER);
DATEPART(MILLISECOND, [ts]) % 1000;

-- === MYSQL ===
EXTRACT(YEAR FROM `ts`);
EXTRACT(QUARTER FROM `ts`);
EXTRACT(MONTH FROM `ts`);
EXTRACT(DAY FROM `ts`);
DAYOFWEEK(`ts`);
EXTRACT(HOUR FROM `ts`);
EXTRACT(MINUTE FROM `ts`);
CAST(EXTRACT(SECOND FROM `ts`) AS SIGNED);
FLOOR(EXTRACT(microsecond FROM `ts`) / 1000);

-- === POSTGRES ===
EXTRACT(YEAR FROM "ts");
EXTRACT(QUARTER FROM "ts");
EXTRACT(MONTH FROM "ts");
EXTRACT(DAY FROM "ts");
EXTRACT(dow FROM "ts") + 1;
EXTRACT(HOUR FROM "ts");
EXTRACT(MINUTE FROM "ts");
CAST(FLOOR(EXTRACT('second' FROM "ts")) AS INT);
CAST(FLOOR(EXTRACT('millisecond' FROM "ts")) AS INT) % 1000;

-- === REDSHIFT ===
EXTRACT(YEAR FROM "ts");
EXTRACT(QUARTER FROM "ts");
EXTRACT(MONTH FROM "ts");
EXTRACT(DAY FROM "ts");
EXTRACT(dow FROM "ts") + 1;
EXTRACT(HOUR FROM "ts");
EXTRACT(MINUTE FROM "ts");
CAST(FLOOR(EXTRACT('second' FROM "ts")) AS INTEGER);
MOD(CAST(FLOOR(EXTRACT('millisecond' FROM "ts")) AS INTEGER), 1000);

-- === SNOWFLAKE ===
DATE_PART(YEAR, "ts");
DATE_PART(QUARTER, "ts");
DATE_PART(MONTH, "ts");
DATE_PART(DAY, "ts");
DATE_PART(DAYOFWEEK, "ts") + 1;
DATE_PART('hour', "ts");
DATE_PART('minute', "ts");
CAST(DATE_PART('second', "ts") AS BIGINT);
DATE_PART('epoch_millisecond', "ts") % 1000;

-- === SPARK ===
EXTRACT(YEAR FROM `ts`);
EXTRACT(QUARTER FROM `ts`);
EXTRACT(MONTH FROM `ts`);
EXTRACT(DAY FROM `ts`);
DAYOFWEEK(TO_DATE(`ts`));
EXTRACT(HOUR FROM `ts`);
EXTRACT(MINUTE FROM `ts`);
CAST(EXTRACT(SECOND FROM `ts`) AS BIGINT);
CAST(DATE_FORMAT(`ts`, 'SSS') AS INT);

-- === TRINO ===
EXTRACT(YEAR FROM "ts");
EXTRACT(QUARTER FROM "ts");
EXTRACT(MONTH FROM "ts");
EXTRACT(DAY FROM "ts");
DAY_OF_WEEK("ts") % 7 + 1;
EXTRACT(HOUR FROM "ts");
EXTRACT(MINUTE FROM "ts");
CAST(EXTRACT(SECOND FROM "ts") AS BIGINT);
MILLISECOND("ts");
""")
