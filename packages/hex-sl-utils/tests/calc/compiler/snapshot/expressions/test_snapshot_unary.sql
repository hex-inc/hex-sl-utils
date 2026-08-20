-- === CALCS ===
-- -numeric_col
-- +numeric_col
-- !bool_col
-- !!bool_col

-- === BIGQUERY ===
-`numeric_col`;
`numeric_col`;
NOT `bool_col`;
NOT (
  NOT `bool_col`
);

-- === CLICKHOUSE ===
-"numeric_col";
"numeric_col";
NOT "bool_col";
NOT (
  NOT "bool_col"
);

-- === DUCKDB ===
-"numeric_col";
"numeric_col";
NOT "bool_col";
NOT (
  NOT "bool_col"
);

-- === MSSQL ===
-[numeric_col];
[numeric_col];
IIF(NOT [bool_col] <> 0, 1, 0);
IIF(NOT (
  NOT [bool_col] <> 0
), 1, 0);

-- === MYSQL ===
-`numeric_col`;
`numeric_col`;
NOT `bool_col`;
NOT (
  NOT `bool_col`
);

-- === POSTGRES ===
-"numeric_col";
"numeric_col";
NOT "bool_col";
NOT (
  NOT "bool_col"
);

-- === REDSHIFT ===
-"numeric_col";
"numeric_col";
NOT "bool_col";
NOT (
  NOT "bool_col"
);

-- === SNOWFLAKE ===
-"numeric_col";
"numeric_col";
NOT "bool_col";
NOT (
  NOT "bool_col"
);

-- === SPARK ===
-`numeric_col`;
`numeric_col`;
NOT `bool_col`;
NOT (
  NOT `bool_col`
);

-- === TRINO ===
-"numeric_col";
"numeric_col";
NOT "bool_col";
NOT (
  NOT "bool_col"
);
