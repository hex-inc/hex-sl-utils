-- === CALCS ===
-- percentile(int_col, 0.5)
-- percentile(float_col, 0.75)

-- === CLICKHOUSE ===
quantileExact(0.5)(CAST("int_col" AS Nullable(Float64)));
quantileExact(0.75)(CAST("float_col" AS Nullable(Float64)));

-- === DUCKDB ===
QUANTILE(CAST("int_col" AS DOUBLE), 0.5);
QUANTILE(CAST("float_col" AS DOUBLE), 0.75);

-- === POSTGRES ===
PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY
  CAST("int_col" AS DOUBLE PRECISION));
PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY
  CAST("float_col" AS DOUBLE PRECISION));

-- === SNOWFLAKE ===
PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY
  CAST("int_col" AS DOUBLE));
PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY
  CAST("float_col" AS DOUBLE));

-- === SPARK ===
PERCENTILE(CAST(`int_col` AS DOUBLE), 0.5);
PERCENTILE(CAST(`float_col` AS DOUBLE), 0.75);
