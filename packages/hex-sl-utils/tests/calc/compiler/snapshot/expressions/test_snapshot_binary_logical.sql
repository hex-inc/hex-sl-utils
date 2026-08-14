-- === CALCS ===
-- bool_col1 AND bool_col2
-- bool_col1 AND TRUE
-- bool_col1 AND FALSE
-- bool_col1 OR bool_col2
-- bool_col1 OR TRUE
-- bool_col1 OR FALSE
-- (bool_col1 AND bool_col2) OR NOT bool_col1
-- bool_col1 AND (int_col > 0)
-- (bool_col1 AND bool_col2) == (bool_col1 OR bool_col2)

-- === BIGQUERY ===
`bool_col1` AND `bool_col2`;
`bool_col1` AND TRUE;
`bool_col1` AND FALSE;
`bool_col1` OR `bool_col2`;
`bool_col1` OR TRUE;
`bool_col1` OR FALSE;
`bool_col1` AND `bool_col2` OR NOT `bool_col1`;
`bool_col1` AND `int_col` > 0;
(
  `bool_col1` AND `bool_col2`
) = (
  `bool_col1` OR `bool_col2`
);

-- === CLICKHOUSE ===
"bool_col1" AND "bool_col2";
"bool_col1" AND TRUE;
"bool_col1" AND FALSE;
"bool_col1" OR "bool_col2";
"bool_col1" OR TRUE;
"bool_col1" OR FALSE;
"bool_col1" AND "bool_col2" OR NOT "bool_col1";
"bool_col1" AND "int_col" > 0;
(
  "bool_col1" AND "bool_col2"
) = (
  "bool_col1" OR "bool_col2"
);

-- === DUCKDB ===
"bool_col1" AND "bool_col2";
"bool_col1" AND TRUE;
"bool_col1" AND FALSE;
"bool_col1" OR "bool_col2";
"bool_col1" OR TRUE;
"bool_col1" OR FALSE;
"bool_col1" AND "bool_col2" OR NOT "bool_col1";
"bool_col1" AND "int_col" > 0;
(
  "bool_col1" AND "bool_col2"
) = (
  "bool_col1" OR "bool_col2"
);

-- === MSSQL ===
IIF([bool_col1] <> 0 AND [bool_col2] <> 0, 1, 0);
IIF([bool_col1] <> 0 AND (1 = 1), 1, 0);
IIF([bool_col1] <> 0 AND (1 = 0), 1, 0);
IIF([bool_col1] <> 0 OR [bool_col2] <> 0, 1, 0);
IIF([bool_col1] <> 0 OR (1 = 1), 1, 0);
IIF([bool_col1] <> 0 OR (1 = 0), 1, 0);
IIF([bool_col1] <> 0 AND [bool_col2] <> 0 OR NOT [bool_col1] <> 0, 1, 0);
IIF([bool_col1] <> 0 AND [int_col] > 0, 1, 0);
IIF(
  IIF([bool_col1] <> 0 AND [bool_col2] <> 0, 1, 0) = IIF([bool_col1] <> 0 OR [bool_col2] <> 0, 1, 0),
  1,
  0
);

-- === MYSQL ===
`bool_col1` AND `bool_col2`;
`bool_col1` AND TRUE;
`bool_col1` AND FALSE;
`bool_col1` OR `bool_col2`;
`bool_col1` OR TRUE;
`bool_col1` OR FALSE;
`bool_col1` AND `bool_col2` OR NOT `bool_col1`;
`bool_col1` AND `int_col` > 0;
(
  `bool_col1` AND `bool_col2`
) = (
  `bool_col1` OR `bool_col2`
);

-- === POSTGRES ===
"bool_col1" AND "bool_col2";
"bool_col1" AND TRUE;
"bool_col1" AND FALSE;
"bool_col1" OR "bool_col2";
"bool_col1" OR TRUE;
"bool_col1" OR FALSE;
"bool_col1" AND "bool_col2" OR NOT "bool_col1";
"bool_col1" AND "int_col" > 0;
(
  "bool_col1" AND "bool_col2"
) = (
  "bool_col1" OR "bool_col2"
);

-- === REDSHIFT ===
"bool_col1" AND "bool_col2";
"bool_col1" AND TRUE;
"bool_col1" AND FALSE;
"bool_col1" OR "bool_col2";
"bool_col1" OR TRUE;
"bool_col1" OR FALSE;
"bool_col1" AND "bool_col2" OR NOT "bool_col1";
"bool_col1" AND "int_col" > 0;
(
  "bool_col1" AND "bool_col2"
) = (
  "bool_col1" OR "bool_col2"
);

-- === SNOWFLAKE ===
"bool_col1" AND "bool_col2";
"bool_col1" AND TRUE;
"bool_col1" AND FALSE;
"bool_col1" OR "bool_col2";
"bool_col1" OR TRUE;
"bool_col1" OR FALSE;
"bool_col1" AND "bool_col2" OR NOT "bool_col1";
"bool_col1" AND "int_col" > 0;
(
  "bool_col1" AND "bool_col2"
) = (
  "bool_col1" OR "bool_col2"
);

-- === SPARK ===
`bool_col1` AND `bool_col2`;
`bool_col1` AND TRUE;
`bool_col1` AND FALSE;
`bool_col1` OR `bool_col2`;
`bool_col1` OR TRUE;
`bool_col1` OR FALSE;
`bool_col1` AND `bool_col2` OR NOT `bool_col1`;
`bool_col1` AND `int_col` > 0;
(
  `bool_col1` AND `bool_col2`
) = (
  `bool_col1` OR `bool_col2`
);

-- === TRINO ===
"bool_col1" AND "bool_col2";
"bool_col1" AND TRUE;
"bool_col1" AND FALSE;
"bool_col1" OR "bool_col2";
"bool_col1" OR TRUE;
"bool_col1" OR FALSE;
"bool_col1" AND "bool_col2" OR NOT "bool_col1";
"bool_col1" AND "int_col" > 0;
(
  "bool_col1" AND "bool_col2"
) = (
  "bool_col1" OR "bool_col2"
);
