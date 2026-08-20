-- === CALCS ===
-- isfinite(float_input)
-- isfinite(int_input)
-- isfinite(str_input)

-- === BIGQUERY ===
NOT (
  `float_input` IS NULL
  OR IS_NAN(CAST(`float_input` AS FLOAT64))
  OR `float_input` = CAST('Infinity' AS FLOAT64)
  OR `float_input` = CAST('-Infinity' AS FLOAT64)
);
NOT (
  `int_input` IS NULL
  OR IS_NAN(CAST(`int_input` AS FLOAT64))
  OR `int_input` = CAST('Infinity' AS FLOAT64)
  OR `int_input` = CAST('-Infinity' AS FLOAT64)
);
NOT `str_input` IS NULL;

-- === CLICKHOUSE ===
NOT (
  "float_input" IS NULL
  OR isNaN(CAST("float_input" AS Nullable(Float64)))
  OR "float_input" = CAST('Infinity' AS Nullable(Float64))
  OR "float_input" = CAST('-Infinity' AS Nullable(Float64))
);
NOT (
  "int_input" IS NULL
  OR isNaN(CAST("int_input" AS Nullable(Float64)))
  OR "int_input" = CAST('Infinity' AS Nullable(Float64))
  OR "int_input" = CAST('-Infinity' AS Nullable(Float64))
);
NOT (
  "str_input" IS NULL
);

-- === DUCKDB ===
NOT (
  "float_input" IS NULL OR ISNAN("float_input") OR ISINF("float_input")
);
NOT (
  "int_input" IS NULL OR ISNAN("int_input") OR ISINF("int_input")
);
NOT "str_input" IS NULL;

-- === MSSQL ===
IIF(NOT [float_input] IS NULL, 1, 0);
IIF(NOT [int_input] IS NULL, 1, 0);
IIF(NOT [str_input] IS NULL, 1, 0);

-- === MYSQL ===
NOT `float_input` IS NULL;
NOT `int_input` IS NULL;
NOT `str_input` IS NULL;

-- === POSTGRES ===
NOT (
  "float_input" IS NULL
  OR CAST("float_input" AS DOUBLE PRECISION) = CAST('NaN' AS DOUBLE PRECISION)
  OR "float_input" = CAST('Infinity' AS DOUBLE PRECISION)
  OR "float_input" = CAST('-Infinity' AS DOUBLE PRECISION)
);
NOT (
  "int_input" IS NULL
  OR CAST("int_input" AS DOUBLE PRECISION) = CAST('NaN' AS DOUBLE PRECISION)
  OR "int_input" = CAST('Infinity' AS DOUBLE PRECISION)
  OR "int_input" = CAST('-Infinity' AS DOUBLE PRECISION)
);
NOT "str_input" IS NULL;

-- === REDSHIFT ===
NOT (
  "float_input" IS NULL
  OR CAST("float_input" AS DOUBLE PRECISION) = CAST('NaN' AS DOUBLE PRECISION)
  OR "float_input" = CAST('Infinity' AS DOUBLE PRECISION)
  OR "float_input" = CAST('-Infinity' AS DOUBLE PRECISION)
);
NOT (
  "int_input" IS NULL
  OR CAST("int_input" AS DOUBLE PRECISION) = CAST('NaN' AS DOUBLE PRECISION)
  OR "int_input" = CAST('Infinity' AS DOUBLE PRECISION)
  OR "int_input" = CAST('-Infinity' AS DOUBLE PRECISION)
);
NOT "str_input" IS NULL;

-- === SNOWFLAKE ===
NOT (
  "float_input" IS NULL
  OR CAST("float_input" AS DOUBLE) = CAST('NaN' AS DOUBLE)
  OR "float_input" = CAST('Infinity' AS DOUBLE)
  OR "float_input" = CAST('-Infinity' AS DOUBLE)
);
NOT (
  "int_input" IS NULL
  OR CAST("int_input" AS DOUBLE) = CAST('NaN' AS DOUBLE)
  OR "int_input" = CAST('Infinity' AS DOUBLE)
  OR "int_input" = CAST('-Infinity' AS DOUBLE)
);
NOT "str_input" IS NULL;

-- === SPARK ===
NOT (
  `float_input` IS NULL
  OR ISNAN(CAST(`float_input` AS DOUBLE))
  OR `float_input` = CAST('Infinity' AS DOUBLE)
  OR `float_input` = CAST('-Infinity' AS DOUBLE)
);
NOT (
  `int_input` IS NULL
  OR ISNAN(CAST(`int_input` AS DOUBLE))
  OR `int_input` = CAST('Infinity' AS DOUBLE)
  OR `int_input` = CAST('-Infinity' AS DOUBLE)
);
NOT `str_input` IS NULL;

-- === TRINO ===
NOT (
  "float_input" IS NULL
  OR IS_NAN(CAST("float_input" AS DOUBLE))
  OR "float_input" = CAST('Infinity' AS DOUBLE)
  OR "float_input" = CAST('-Infinity' AS DOUBLE)
);
NOT (
  "int_input" IS NULL
  OR IS_NAN(CAST("int_input" AS DOUBLE))
  OR "int_input" = CAST('Infinity' AS DOUBLE)
  OR "int_input" = CAST('-Infinity' AS DOUBLE)
);
NOT "str_input" IS NULL;
