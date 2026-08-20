-- === CALCS ===
-- median(int_col)
-- median(float_col)

-- === CLICKHOUSE ===
median(CAST("int_col" AS Nullable(Float64)));
median(CAST("float_col" AS Nullable(Float64)));

-- === DUCKDB ===
MEDIAN(CAST("int_col" AS DOUBLE));
MEDIAN(CAST("float_col" AS DOUBLE));

-- === POSTGRES ===
PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY
  CAST("int_col" AS DOUBLE PRECISION));
PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY
  CAST("float_col" AS DOUBLE PRECISION));

-- === SNOWFLAKE ===
MEDIAN(CAST("int_col" AS DOUBLE));
MEDIAN(CAST("float_col" AS DOUBLE));

-- === SPARK ===
PERCENTILE(CAST(`int_col` AS DOUBLE), 0.5);
PERCENTILE(CAST(`float_col` AS DOUBLE), 0.5);
