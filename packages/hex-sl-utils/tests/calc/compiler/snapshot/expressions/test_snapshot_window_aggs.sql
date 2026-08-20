-- === CALCS ===
-- max(numeric_col)
-- sum(numeric_col)
-- mean(numeric_col)
-- stddev(numeric_col)
-- variance(var_col)
-- variancepop(var_col)
-- count()
-- count(null_col)

-- === BIGQUERY ===
MAX(`numeric_col`) OVER ();
SUM(`numeric_col`) OVER ();
AVG(CAST(`numeric_col` AS FLOAT64)) OVER ();
STDDEV_SAMP(CAST(`numeric_col` AS FLOAT64)) OVER ();
VARIANCE(CAST(`var_col` AS FLOAT64)) OVER ();
VAR_POP(CAST(`var_col` AS FLOAT64)) OVER ();
COUNT(1) OVER ();
COUNT(`null_col`) OVER ();

-- === CLICKHOUSE ===
MAX("numeric_col") OVER ();
SUM("numeric_col") OVER ();
AVG(CAST("numeric_col" AS Nullable(Float64))) OVER ();
STDDEV_SAMP(CAST("numeric_col" AS Nullable(Float64))) OVER ();
varSamp(CAST("var_col" AS Nullable(Float64))) OVER ();
varPop(CAST("var_col" AS Nullable(Float64))) OVER ();
COUNT(1) OVER ();
COUNT("null_col") OVER ();

-- === DUCKDB ===
MAX("numeric_col") OVER ();
SUM("numeric_col") OVER ();
AVG(CAST("numeric_col" AS DOUBLE)) OVER ();
STDDEV_SAMP(CAST("numeric_col" AS DOUBLE)) OVER ();
VARIANCE(CAST("var_col" AS DOUBLE)) OVER ();
VAR_POP(CAST("var_col" AS DOUBLE)) OVER ();
COUNT(1) OVER ();
COUNT("null_col") OVER ();

-- === MSSQL ===
MAX([numeric_col]) OVER ();
SUM([numeric_col]) OVER ();
AVG(CAST([numeric_col] AS FLOAT)) OVER ();
STDEV(CAST([numeric_col] AS FLOAT)) OVER ();
VAR(CAST([var_col] AS FLOAT)) OVER ();
VARP(CAST([var_col] AS FLOAT)) OVER ();
COUNT(*) OVER ();
COUNT([null_col]) OVER ();

-- === MYSQL ===
MAX(`numeric_col`) OVER ();
SUM(`numeric_col`) OVER ();
AVG(CAST(`numeric_col` AS DOUBLE)) OVER ();
STDDEV_SAMP(CAST(`numeric_col` AS DOUBLE)) OVER ();
VAR_SAMP(CAST(`var_col` AS DOUBLE)) OVER ();
VAR_POP(CAST(`var_col` AS DOUBLE)) OVER ();
COUNT(1) OVER ();
COUNT(`null_col`) OVER ();

-- === POSTGRES ===
MAX("numeric_col") OVER ();
SUM("numeric_col") OVER ();
AVG(CAST("numeric_col" AS DOUBLE PRECISION)) OVER ();
STDDEV_SAMP(CAST("numeric_col" AS DOUBLE PRECISION)) OVER ();
VAR_SAMP(CAST("var_col" AS DOUBLE PRECISION)) OVER ();
VAR_POP(CAST("var_col" AS DOUBLE PRECISION)) OVER ();
COUNT(1) OVER ();
COUNT("null_col") OVER ();

-- === REDSHIFT ===
MAX("numeric_col") OVER ();
SUM("numeric_col") OVER ();
AVG(CAST("numeric_col" AS DOUBLE PRECISION)) OVER ();
STDDEV_SAMP(CAST("numeric_col" AS DOUBLE PRECISION)) OVER ();
VAR_SAMP(CAST("var_col" AS DOUBLE PRECISION)) OVER ();
VAR_POP(CAST("var_col" AS DOUBLE PRECISION)) OVER ();
COUNT(1) OVER ();
COUNT("null_col") OVER ();

-- === SNOWFLAKE ===
MAX("numeric_col") OVER ();
SUM("numeric_col") OVER ();
AVG(CAST("numeric_col" AS DOUBLE)) OVER ();
STDDEV_SAMP(CAST("numeric_col" AS DOUBLE)) OVER ();
VARIANCE(CAST("var_col" AS DOUBLE)) OVER ();
VARIANCE_POP(CAST("var_col" AS DOUBLE)) OVER ();
COUNT(1) OVER ();
COUNT("null_col") OVER ();

-- === SPARK ===
MAX(`numeric_col`) OVER ();
SUM(`numeric_col`) OVER ();
AVG(CAST(`numeric_col` AS DOUBLE)) OVER ();
STDDEV_SAMP(CAST(`numeric_col` AS DOUBLE)) OVER ();
VARIANCE(CAST(`var_col` AS DOUBLE)) OVER ();
VAR_POP(CAST(`var_col` AS DOUBLE)) OVER ();
COUNT(1) OVER ();
COUNT(`null_col`) OVER ();

-- === TRINO ===
MAX("numeric_col") OVER ();
SUM("numeric_col") OVER ();
AVG(CAST("numeric_col" AS DOUBLE)) OVER ();
STDDEV_SAMP(CAST("numeric_col" AS DOUBLE)) OVER ();
VARIANCE(CAST("var_col" AS DOUBLE)) OVER ();
VAR_POP(CAST("var_col" AS DOUBLE)) OVER ();
COUNT(1) OVER ();
COUNT("null_col") OVER ();
