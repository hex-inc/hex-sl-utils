-- === CALCS ===
-- lhs < rhs
-- lhs <= rhs
-- lhs <= rhs
-- lhs > rhs
-- lhs >= rhs
-- lhs >= rhs
-- lhs == rhs
-- lhs != rhs
-- lhs != rhs

-- === BIGQUERY ===
`lhs` < `rhs`;
`lhs` <= `rhs`;
`lhs` <= `rhs`;
`lhs` > `rhs`;
`lhs` >= `rhs`;
`lhs` >= `rhs`;
`lhs` = `rhs`;
`lhs` <> `rhs`;
`lhs` <> `rhs`;

-- === CLICKHOUSE ===
"lhs" < "rhs";
"lhs" <= "rhs";
"lhs" <= "rhs";
"lhs" > "rhs";
"lhs" >= "rhs";
"lhs" >= "rhs";
"lhs" = "rhs";
"lhs" <> "rhs";
"lhs" <> "rhs";

-- === DUCKDB ===
"lhs" < "rhs";
"lhs" <= "rhs";
"lhs" <= "rhs";
"lhs" > "rhs";
"lhs" >= "rhs";
"lhs" >= "rhs";
"lhs" = "rhs";
"lhs" <> "rhs";
"lhs" <> "rhs";

-- === MSSQL ===
IIF([lhs] < [rhs], 1, 0);
IIF([lhs] <= [rhs], 1, 0);
IIF([lhs] <= [rhs], 1, 0);
IIF([lhs] > [rhs], 1, 0);
IIF([lhs] >= [rhs], 1, 0);
IIF([lhs] >= [rhs], 1, 0);
IIF([lhs] = [rhs], 1, 0);
IIF([lhs] <> [rhs], 1, 0);
IIF([lhs] <> [rhs], 1, 0);

-- === MYSQL ===
`lhs` < `rhs`;
`lhs` <= `rhs`;
`lhs` <= `rhs`;
`lhs` > `rhs`;
`lhs` >= `rhs`;
`lhs` >= `rhs`;
`lhs` = `rhs`;
`lhs` <> `rhs`;
`lhs` <> `rhs`;

-- === POSTGRES ===
"lhs" < "rhs";
"lhs" <= "rhs";
"lhs" <= "rhs";
"lhs" > "rhs";
"lhs" >= "rhs";
"lhs" >= "rhs";
"lhs" = "rhs";
"lhs" <> "rhs";
"lhs" <> "rhs";

-- === REDSHIFT ===
"lhs" < "rhs";
"lhs" <= "rhs";
"lhs" <= "rhs";
"lhs" > "rhs";
"lhs" >= "rhs";
"lhs" >= "rhs";
"lhs" = "rhs";
"lhs" <> "rhs";
"lhs" <> "rhs";

-- === SNOWFLAKE ===
"lhs" < "rhs";
"lhs" <= "rhs";
"lhs" <= "rhs";
"lhs" > "rhs";
"lhs" >= "rhs";
"lhs" >= "rhs";
"lhs" = "rhs";
"lhs" <> "rhs";
"lhs" <> "rhs";

-- === SPARK ===
`lhs` < `rhs`;
`lhs` <= `rhs`;
`lhs` <= `rhs`;
`lhs` > `rhs`;
`lhs` >= `rhs`;
`lhs` >= `rhs`;
`lhs` = `rhs`;
`lhs` <> `rhs`;
`lhs` <> `rhs`;

-- === TRINO ===
"lhs" < "rhs";
"lhs" <= "rhs";
"lhs" <= "rhs";
"lhs" > "rhs";
"lhs" >= "rhs";
"lhs" >= "rhs";
"lhs" = "rhs";
"lhs" <> "rhs";
"lhs" <> "rhs";
