-- === CALCS ===
-- if(lhs > 0, lhs, -100)
-- isnull(nullable)
-- isoneof(lhs, 1, 2, 3)
-- isfinite(lhs)
-- switch(switch_input, 1, 'A', 2, 'B', 3, 'C')
-- switch(switch_input, 1, 'A', 2, 'B', 3, 'C', 'Other')

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
