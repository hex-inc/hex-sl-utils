-- === CALCS ===
-- min(numeric_col)
-- max(numeric_col)
-- sum(numeric_col)
-- mean(numeric_col)
-- stddev(numeric_col)
-- stddevpop(numeric_col)
-- variance(var_col)
-- variancepop(var_col)
-- count()
-- count(null_col)
-- countdistinct(null_col)
-- sumboolean(boolean_col)
-- sumboolean(boolean_num_col)

-- === BIGQUERY ===
MIN(`numeric_col`);
MAX(`numeric_col`);
SUM(`numeric_col`);
AVG(CAST(`numeric_col` AS FLOAT64));
STDDEV_SAMP(CAST(`numeric_col` AS FLOAT64));
STDDEV_POP(CAST(`numeric_col` AS FLOAT64));
VARIANCE(CAST(`var_col` AS FLOAT64));
VAR_POP(CAST(`var_col` AS FLOAT64));
COUNT(1);
COUNT(`null_col`);
COUNT(DISTINCT `null_col`);
SUM(CASE WHEN `boolean_col` THEN 1 ELSE 0 END);
SUM(CASE WHEN `boolean_num_col` <> 0 THEN 1 ELSE 0 END);

-- === CLICKHOUSE ===
MIN("numeric_col");
MAX("numeric_col");
SUM("numeric_col");
AVG(CAST("numeric_col" AS Nullable(Float64)));
STDDEV_SAMP(CAST("numeric_col" AS Nullable(Float64)));
STDDEV_POP(CAST("numeric_col" AS Nullable(Float64)));
varSamp(CAST("var_col" AS Nullable(Float64)));
varPop(CAST("var_col" AS Nullable(Float64)));
COUNT(1);
COUNT("null_col");
COUNT(DISTINCT "null_col");
SUM(CASE WHEN "boolean_col" THEN 1 ELSE 0 END);
SUM(CASE WHEN "boolean_num_col" <> 0 THEN 1 ELSE 0 END);

-- === DUCKDB ===
MIN("numeric_col");
MAX("numeric_col");
SUM("numeric_col");
AVG(CAST("numeric_col" AS DOUBLE));
STDDEV_SAMP(CAST("numeric_col" AS DOUBLE));
STDDEV_POP(CAST("numeric_col" AS DOUBLE));
VARIANCE(CAST("var_col" AS DOUBLE));
VAR_POP(CAST("var_col" AS DOUBLE));
COUNT(1);
COUNT("null_col");
COUNT(DISTINCT "null_col");
SUM(CASE WHEN "boolean_col" THEN 1 ELSE 0 END);
SUM(CASE WHEN "boolean_num_col" <> 0 THEN 1 ELSE 0 END);

-- === MSSQL ===
MIN([numeric_col]);
MAX([numeric_col]);
SUM([numeric_col]);
AVG(CAST([numeric_col] AS FLOAT));
STDEV(CAST([numeric_col] AS FLOAT));
STDEVP(CAST([numeric_col] AS FLOAT));
VAR(CAST([var_col] AS FLOAT));
VARP(CAST([var_col] AS FLOAT));
COUNT(1);
COUNT([null_col]);
COUNT(DISTINCT [null_col]);
SUM(CASE WHEN [boolean_col] <> 0 THEN 1 ELSE 0 END);
SUM(CASE WHEN [boolean_num_col] <> 0 THEN 1 ELSE 0 END);

-- === MYSQL ===
MIN(`numeric_col`);
MAX(`numeric_col`);
SUM(`numeric_col`);
AVG(CAST(`numeric_col` AS DOUBLE));
STDDEV_SAMP(CAST(`numeric_col` AS DOUBLE));
STDDEV_POP(CAST(`numeric_col` AS DOUBLE));
VAR_SAMP(CAST(`var_col` AS DOUBLE));
VAR_POP(CAST(`var_col` AS DOUBLE));
COUNT(1);
COUNT(`null_col`);
COUNT(DISTINCT `null_col`);
SUM(CASE WHEN `boolean_col` THEN 1 ELSE 0 END);
SUM(CASE WHEN `boolean_num_col` <> 0 THEN 1 ELSE 0 END);

-- === POSTGRES ===
MIN("numeric_col");
MAX("numeric_col");
SUM("numeric_col");
AVG(CAST("numeric_col" AS DOUBLE PRECISION));
STDDEV_SAMP(CAST("numeric_col" AS DOUBLE PRECISION));
STDDEV_POP(CAST("numeric_col" AS DOUBLE PRECISION));
VAR_SAMP(CAST("var_col" AS DOUBLE PRECISION));
VAR_POP(CAST("var_col" AS DOUBLE PRECISION));
COUNT(1);
COUNT("null_col");
COUNT(DISTINCT "null_col");
SUM(CASE WHEN "boolean_col" THEN 1 ELSE 0 END);
SUM(CASE WHEN "boolean_num_col" <> 0 THEN 1 ELSE 0 END);

-- === REDSHIFT ===
MIN("numeric_col");
MAX("numeric_col");
SUM("numeric_col");
AVG(CAST("numeric_col" AS DOUBLE PRECISION));
STDDEV_SAMP(CAST("numeric_col" AS DOUBLE PRECISION));
STDDEV_POP(CAST("numeric_col" AS DOUBLE PRECISION));
VAR_SAMP(CAST("var_col" AS DOUBLE PRECISION));
VAR_POP(CAST("var_col" AS DOUBLE PRECISION));
COUNT(1);
COUNT("null_col");
COUNT(DISTINCT "null_col");
SUM(CASE WHEN "boolean_col" THEN 1 ELSE 0 END);
SUM(CASE WHEN "boolean_num_col" <> 0 THEN 1 ELSE 0 END);

-- === SNOWFLAKE ===
MIN("numeric_col");
MAX("numeric_col");
SUM("numeric_col");
AVG(CAST("numeric_col" AS DOUBLE));
STDDEV_SAMP(CAST("numeric_col" AS DOUBLE));
STDDEV_POP(CAST("numeric_col" AS DOUBLE));
VARIANCE(CAST("var_col" AS DOUBLE));
VARIANCE_POP(CAST("var_col" AS DOUBLE));
COUNT(1);
COUNT("null_col");
COUNT(DISTINCT "null_col");
SUM(CASE WHEN "boolean_col" THEN 1 ELSE 0 END);
SUM(CASE WHEN "boolean_num_col" <> 0 THEN 1 ELSE 0 END);

-- === SPARK ===
MIN(`numeric_col`);
MAX(`numeric_col`);
SUM(`numeric_col`);
AVG(CAST(`numeric_col` AS DOUBLE));
STDDEV_SAMP(CAST(`numeric_col` AS DOUBLE));
STDDEV_POP(CAST(`numeric_col` AS DOUBLE));
VARIANCE(CAST(`var_col` AS DOUBLE));
VAR_POP(CAST(`var_col` AS DOUBLE));
COUNT(1);
COUNT(`null_col`);
COUNT(DISTINCT `null_col`);
SUM(CASE WHEN `boolean_col` THEN 1 ELSE 0 END);
SUM(CASE WHEN `boolean_num_col` <> 0 THEN 1 ELSE 0 END);

-- === TRINO ===
MIN("numeric_col");
MAX("numeric_col");
SUM("numeric_col");
AVG(CAST("numeric_col" AS DOUBLE));
STDDEV_SAMP(CAST("numeric_col" AS DOUBLE));
STDDEV_POP(CAST("numeric_col" AS DOUBLE));
VARIANCE(CAST("var_col" AS DOUBLE));
VAR_POP(CAST("var_col" AS DOUBLE));
COUNT(1);
COUNT("null_col");
COUNT(DISTINCT "null_col");
SUM(CASE WHEN "boolean_col" THEN 1 ELSE 0 END);
SUM(CASE WHEN "boolean_num_col" <> 0 THEN 1 ELSE 0 END);
