-- === CALCS ===
-- percentileapprox(int_col, 0.5)
-- percentileapprox(float_col, 0.75)

-- === BIGQUERY ===
APPROX_QUANTILES(CAST(`int_col` AS FLOAT64), 100)[OFFSET(50)];
APPROX_QUANTILES(CAST(`float_col` AS FLOAT64), 100)[OFFSET(75)];

-- === CLICKHOUSE ===
quantileTDigest(0.5)(CAST("int_col" AS Nullable(Float64)));
quantileTDigest(0.75)(CAST("float_col" AS Nullable(Float64)));

-- === DUCKDB ===
APPROX_QUANTILE(CAST("int_col" AS DOUBLE), 0.5);
APPROX_QUANTILE(CAST("float_col" AS DOUBLE), 0.75);

-- === SNOWFLAKE ===
APPROX_PERCENTILE(CAST("int_col" AS DOUBLE), 0.5);
APPROX_PERCENTILE(CAST("float_col" AS DOUBLE), 0.75);

-- === SPARK ===
PERCENTILE_APPROX(CAST(`int_col` AS DOUBLE), 0.5);
PERCENTILE_APPROX(CAST(`float_col` AS DOUBLE), 0.75);

-- === TRINO ===
APPROX_PERCENTILE(CAST("int_col" AS DOUBLE), 0.5);
APPROX_PERCENTILE(CAST("float_col" AS DOUBLE), 0.75);
