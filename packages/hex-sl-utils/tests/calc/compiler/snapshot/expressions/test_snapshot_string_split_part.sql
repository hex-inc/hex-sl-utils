-- === CALCS ===
-- splitPart(values, 'NEVER', 1)
-- delimiter
-- part_number
-- splitPart(values, delimiter, part_number)

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
  ELSE COALESCE(SPLIT(`values`, CONCAT('\\Q', 'NEVER', '\\E'))[CAST(1 AS INT) - 1], '')
END;
`delimiter`;
`part_number`;
CASE
  WHEN `values` IS NULL
  THEN NULL
  ELSE COALESCE(
    SPLIT(`values`, CONCAT('\\Q', `delimiter`, '\\E'))[CAST(`part_number` AS INT) - 1],
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
