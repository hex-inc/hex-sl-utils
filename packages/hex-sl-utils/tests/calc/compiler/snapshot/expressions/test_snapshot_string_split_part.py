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
    dialect_name = SnapshotTest.result_dialect
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


# SQL expression snapshots


def test_snapshot_string_split_part_sql():
    """Snapshot directly compiled calc SQL for every supported dialect."""
    assert SnapshotTest.render_sql_snapshot() == snapshot("""\
-- === BIGQUERY ===
IF(
  `values` IS NULL,
  NULL,
  COALESCE(SPLIT(`values`, 'NEVER')[safe_offset(CAST(trunc(1) AS INT64) - 1)], '')
);
`delimiter`;
`part_number`;
IF(
  `values` IS NULL,
  NULL,
  COALESCE(
    SPLIT(`values`, `delimiter`)[safe_offset(CAST(trunc(`part_number`) AS INT64) - 1)],
    ''
  )
);

-- === CLICKHOUSE ===
CASE
  WHEN "values" IS NULL
  THEN NULL
  WHEN 1 > LENGTH(
    splitByString(
      '___hex_sl_clickhouse_delimiter_substitution___',
      replaceAll(COALESCE("values", ''), 'NEVER', '___hex_sl_clickhouse_delimiter_substitution___')
    )
  )
  THEN ''
  ELSE splitByString(
    '___hex_sl_clickhouse_delimiter_substitution___',
    replaceAll(COALESCE("values", ''), 'NEVER', '___hex_sl_clickhouse_delimiter_substitution___')
  )[1]
END;
"delimiter";
"part_number";
CASE
  WHEN "values" IS NULL
  THEN NULL
  WHEN "part_number" > LENGTH(
    splitByString(
      '___hex_sl_clickhouse_delimiter_substitution___',
      replaceAll(
        COALESCE("values", ''),
        "delimiter",
        '___hex_sl_clickhouse_delimiter_substitution___'
      )
    )
  )
  THEN ''
  ELSE splitByString(
    '___hex_sl_clickhouse_delimiter_substitution___',
    replaceAll(
      COALESCE("values", ''),
      "delimiter",
      '___hex_sl_clickhouse_delimiter_substitution___'
    )
  )["part_number"]
END;

-- === DUCKDB ===
SPLIT_PART("values", 'NEVER', 1);
"delimiter";
"part_number";
SPLIT_PART("values", "delimiter", "part_number");

-- === MSSQL ===
LEFT(
  [values],
  CHARINDEX('NEVER', CONCAT([values], 'NEVER') COLLATE Latin1_General_BIN2) - 1
);
[delimiter];
[part_number];
CASE
  WHEN [part_number] = 1
  THEN LEFT(
    [values],
    CHARINDEX([delimiter], CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2) - 1
  )
  WHEN [part_number] = 2
  THEN IIF(
    CHARINDEX(
      [delimiter],
      CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2,
      CHARINDEX([delimiter], CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2) + DATALENGTH([delimiter])
    ) - (
      CHARINDEX(
        [delimiter],
        CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2,
        CHARINDEX([delimiter], CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2)
      ) + DATALENGTH([delimiter])
    ) < 0,
    '',
    SUBSTRING(
      [values],
      CHARINDEX(
        [delimiter],
        CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2,
        CHARINDEX([delimiter], CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2)
      ) + DATALENGTH([delimiter]),
      CHARINDEX(
        [delimiter],
        CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2,
        CHARINDEX([delimiter], CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2) + DATALENGTH([delimiter])
      ) - (
        CHARINDEX(
          [delimiter],
          CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2,
          CHARINDEX([delimiter], CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2)
        ) + DATALENGTH([delimiter])
      )
    )
  )
  WHEN [part_number] = 3
  THEN IIF(
    CHARINDEX(
      [delimiter],
      CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2,
      CHARINDEX(
        [delimiter],
        CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2,
        CHARINDEX([delimiter], CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2) + DATALENGTH([delimiter])
      ) + DATALENGTH([delimiter])
    ) - (
      CHARINDEX(
        [delimiter],
        CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2,
        CHARINDEX(
          [delimiter],
          CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2,
          CHARINDEX([delimiter], CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2) + DATALENGTH([delimiter])
        )
      ) + DATALENGTH([delimiter])
    ) < 0,
    '',
    SUBSTRING(
      [values],
      CHARINDEX(
        [delimiter],
        CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2,
        CHARINDEX(
          [delimiter],
          CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2,
          CHARINDEX([delimiter], CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2) + DATALENGTH([delimiter])
        )
      ) + DATALENGTH([delimiter]),
      CHARINDEX(
        [delimiter],
        CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2,
        CHARINDEX(
          [delimiter],
          CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2,
          CHARINDEX([delimiter], CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2) + DATALENGTH([delimiter])
        ) + DATALENGTH([delimiter])
      ) - (
        CHARINDEX(
          [delimiter],
          CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2,
          CHARINDEX(
            [delimiter],
            CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2,
            CHARINDEX([delimiter], CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2) + DATALENGTH([delimiter])
          )
        ) + DATALENGTH([delimiter])
      )
    )
  )
  WHEN [part_number] = 4
  THEN IIF(
    CHARINDEX(
      [delimiter],
      CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2,
      CHARINDEX(
        [delimiter],
        CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2,
        CHARINDEX(
          [delimiter],
          CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2,
          CHARINDEX([delimiter], CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2) + DATALENGTH([delimiter])
        ) + DATALENGTH([delimiter])
      ) + DATALENGTH([delimiter])
    ) - (
      CHARINDEX(
        [delimiter],
        CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2,
        CHARINDEX(
          [delimiter],
          CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2,
          CHARINDEX(
            [delimiter],
            CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2,
            CHARINDEX([delimiter], CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2) + DATALENGTH([delimiter])
          ) + DATALENGTH([delimiter])
        )
      ) + DATALENGTH([delimiter])
    ) < 0,
    '',
    SUBSTRING(
      [values],
      CHARINDEX(
        [delimiter],
        CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2,
        CHARINDEX(
          [delimiter],
          CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2,
          CHARINDEX(
            [delimiter],
            CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2,
            CHARINDEX([delimiter], CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2) + DATALENGTH([delimiter])
          ) + DATALENGTH([delimiter])
        )
      ) + DATALENGTH([delimiter]),
      CHARINDEX(
        [delimiter],
        CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2,
        CHARINDEX(
          [delimiter],
          CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2,
          CHARINDEX(
            [delimiter],
            CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2,
            CHARINDEX([delimiter], CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2) + DATALENGTH([delimiter])
          ) + DATALENGTH([delimiter])
        ) + DATALENGTH([delimiter])
      ) - (
        CHARINDEX(
          [delimiter],
          CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2,
          CHARINDEX(
            [delimiter],
            CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2,
            CHARINDEX(
              [delimiter],
              CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2,
              CHARINDEX([delimiter], CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2) + DATALENGTH([delimiter])
            ) + DATALENGTH([delimiter])
          )
        ) + DATALENGTH([delimiter])
      )
    )
  )
  WHEN [part_number] = 5
  THEN IIF(
    CHARINDEX(
      [delimiter],
      CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2,
      CHARINDEX(
        [delimiter],
        CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2,
        CHARINDEX(
          [delimiter],
          CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2,
          CHARINDEX(
            [delimiter],
            CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2,
            CHARINDEX([delimiter], CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2) + DATALENGTH([delimiter])
          ) + DATALENGTH([delimiter])
        ) + DATALENGTH([delimiter])
      ) + DATALENGTH([delimiter])
    ) - (
      CHARINDEX(
        [delimiter],
        CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2,
        CHARINDEX(
          [delimiter],
          CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2,
          CHARINDEX(
            [delimiter],
            CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2,
            CHARINDEX(
              [delimiter],
              CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2,
              CHARINDEX([delimiter], CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2) + DATALENGTH([delimiter])
            ) + DATALENGTH([delimiter])
          ) + DATALENGTH([delimiter])
        )
      ) + DATALENGTH([delimiter])
    ) < 0,
    '',
    SUBSTRING(
      [values],
      CHARINDEX(
        [delimiter],
        CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2,
        CHARINDEX(
          [delimiter],
          CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2,
          CHARINDEX(
            [delimiter],
            CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2,
            CHARINDEX(
              [delimiter],
              CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2,
              CHARINDEX([delimiter], CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2) + DATALENGTH([delimiter])
            ) + DATALENGTH([delimiter])
          ) + DATALENGTH([delimiter])
        )
      ) + DATALENGTH([delimiter]),
      CHARINDEX(
        [delimiter],
        CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2,
        CHARINDEX(
          [delimiter],
          CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2,
          CHARINDEX(
            [delimiter],
            CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2,
            CHARINDEX(
              [delimiter],
              CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2,
              CHARINDEX([delimiter], CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2) + DATALENGTH([delimiter])
            ) + DATALENGTH([delimiter])
          ) + DATALENGTH([delimiter])
        ) + DATALENGTH([delimiter])
      ) - (
        CHARINDEX(
          [delimiter],
          CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2,
          CHARINDEX(
            [delimiter],
            CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2,
            CHARINDEX(
              [delimiter],
              CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2,
              CHARINDEX(
                [delimiter],
                CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2,
                CHARINDEX([delimiter], CONCAT([values], [delimiter]) COLLATE Latin1_General_BIN2) + DATALENGTH([delimiter])
              ) + DATALENGTH([delimiter])
            ) + DATALENGTH([delimiter])
          )
        ) + DATALENGTH([delimiter])
      )
    )
  )
  ELSE NULL
END;

-- === MYSQL ===
SUBSTRING_INDEX(SUBSTRING_INDEX(CONCAT(`values`, 'NEVER'), 'NEVER', 1), 'NEVER', -1);
`delimiter`;
`part_number`;
SUBSTRING_INDEX(
  SUBSTRING_INDEX(CONCAT(`values`, `delimiter`), `delimiter`, `part_number`),
  `delimiter`,
  -1
);

-- === POSTGRES ===
SPLIT_PART("values", 'NEVER', 1);
"delimiter";
"part_number";
SPLIT_PART("values", "delimiter", "part_number");

-- === REDSHIFT ===
SPLIT_PART("values", CAST('NEVER' AS VARCHAR(MAX)), 1);
"delimiter";
"part_number";
SPLIT_PART("values", "delimiter", "part_number");

-- === SNOWFLAKE ===
SPLIT_PART("values", 'NEVER', 1);
"delimiter";
"part_number";
SPLIT_PART("values", "delimiter", "part_number");

-- === SPARK ===
CASE
  WHEN `values` IS NULL
  THEN NULL
  ELSE COALESCE(SPLIT(`values`, CONCAT('\\\\Q', 'NEVER', '\\\\E'))[CAST(1 AS INT) - 1], '')
END;
`delimiter`;
`part_number`;
CASE
  WHEN `values` IS NULL
  THEN NULL
  ELSE COALESCE(
    SPLIT(`values`, CONCAT('\\\\Q', `delimiter`, '\\\\E'))[CAST(`part_number` AS INT) - 1],
    ''
  )
END;

-- === TRINO ===
IF("values" IS NULL, NULL, COALESCE(SPLIT_PART("values", 'NEVER', 1), ''));
"delimiter";
"part_number";
IF(
  "values" IS NULL,
  NULL,
  COALESCE(SPLIT_PART("values", "delimiter", "part_number"), '')
);
""")
