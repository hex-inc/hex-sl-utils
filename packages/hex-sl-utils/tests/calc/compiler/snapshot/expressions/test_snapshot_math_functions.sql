-- === CALCS ===
-- abs(int_col)
-- round(float_col)
-- ceil(float_col)
-- floor(float_col)
-- sqrt(trig_col)
-- exp(trig_col)
-- sin(trig_col)
-- cos(trig_col)
-- tan(trig_col)
-- cot(trig_col)

-- === BIGQUERY ===
ABS(`int_col`);
ROUND(`float_col`);
CEIL(CAST(`float_col` AS FLOAT64));
FLOOR(CAST(`float_col` AS FLOAT64));
SQRT(CAST(`trig_col` AS FLOAT64));
EXP(CAST(`trig_col` AS FLOAT64));
SIN(CAST(`trig_col` AS FLOAT64));
COS(CAST(`trig_col` AS FLOAT64));
TAN(CAST(`trig_col` AS FLOAT64));
CASE WHEN `trig_col` = 0 THEN NULL ELSE COT(CAST(`trig_col` AS FLOAT64)) END;

-- === CLICKHOUSE ===
ABS("int_col");
ROUND("float_col");
CEIL(CAST("float_col" AS Nullable(Float64)));
FLOOR(CAST("float_col" AS Nullable(Float64)));
SQRT(CAST("trig_col" AS Nullable(Float64)));
EXP(CAST("trig_col" AS Nullable(Float64)));
SIN(CAST("trig_col" AS Nullable(Float64)));
COS(CAST("trig_col" AS Nullable(Float64)));
TAN(CAST("trig_col" AS Nullable(Float64)));
CASE
  WHEN "trig_col" = 0
  THEN NULL
  ELSE 1.0 / TAN(CAST("trig_col" AS Nullable(Float64)))
END;

-- === DUCKDB ===
ABS("int_col");
ROUND("float_col");
CEIL(CAST("float_col" AS DOUBLE));
FLOOR(CAST("float_col" AS DOUBLE));
SQRT(CAST("trig_col" AS DOUBLE));
EXP(CAST("trig_col" AS DOUBLE));
SIN(CAST("trig_col" AS DOUBLE));
COS(CAST("trig_col" AS DOUBLE));
TAN(CAST("trig_col" AS DOUBLE));
CASE WHEN "trig_col" = 0 THEN NULL ELSE COT(CAST("trig_col" AS DOUBLE)) END;

-- === MSSQL ===
ABS([int_col]);
ROUND([float_col], 0);
CEILING(CAST([float_col] AS FLOAT));
FLOOR(CAST([float_col] AS FLOAT));
SQRT(CAST([trig_col] AS FLOAT));
EXP(CAST([trig_col] AS FLOAT));
SIN(CAST([trig_col] AS FLOAT));
COS(CAST([trig_col] AS FLOAT));
TAN(CAST([trig_col] AS FLOAT));
CASE
  WHEN [trig_col] = 0
  THEN NULL
  ELSE CAST(1.0 AS FLOAT) / TAN(CAST([trig_col] AS FLOAT))
END;

-- === MYSQL ===
ABS(`int_col`);
ROUND(`float_col`);
CEIL(CAST(`float_col` AS DOUBLE));
FLOOR(CAST(`float_col` AS DOUBLE));
SQRT(CAST(`trig_col` AS DOUBLE));
EXP(CAST(`trig_col` AS DOUBLE));
SIN(CAST(`trig_col` AS DOUBLE));
COS(CAST(`trig_col` AS DOUBLE));
TAN(CAST(`trig_col` AS DOUBLE));
CASE WHEN `trig_col` = 0 THEN NULL ELSE COT(CAST(`trig_col` AS DOUBLE)) END;

-- === POSTGRES ===
ABS("int_col");
ROUND("float_col");
CEIL(CAST("float_col" AS DOUBLE PRECISION));
FLOOR(CAST("float_col" AS DOUBLE PRECISION));
SQRT(CAST("trig_col" AS DOUBLE PRECISION));
EXP(CAST("trig_col" AS DOUBLE PRECISION));
SIN(CAST("trig_col" AS DOUBLE PRECISION));
COS(CAST("trig_col" AS DOUBLE PRECISION));
TAN(CAST("trig_col" AS DOUBLE PRECISION));
CASE
  WHEN "trig_col" = 0
  THEN NULL
  ELSE COT(CAST("trig_col" AS DOUBLE PRECISION))
END;

-- === REDSHIFT ===
ABS("int_col");
ROUND("float_col");
CEIL(CAST("float_col" AS DOUBLE PRECISION));
FLOOR(CAST("float_col" AS DOUBLE PRECISION));
SQRT(CAST("trig_col" AS DOUBLE PRECISION));
EXP(CAST("trig_col" AS DOUBLE PRECISION));
SIN(CAST("trig_col" AS DOUBLE PRECISION));
COS(CAST("trig_col" AS DOUBLE PRECISION));
TAN(CAST("trig_col" AS DOUBLE PRECISION));
CASE
  WHEN "trig_col" = 0
  THEN NULL
  ELSE COT(CAST("trig_col" AS DOUBLE PRECISION))
END;

-- === SNOWFLAKE ===
ABS("int_col");
ROUND("float_col");
CEIL(CAST("float_col" AS DOUBLE));
FLOOR(CAST("float_col" AS DOUBLE));
SQRT(CAST("trig_col" AS DOUBLE));
EXP(CAST("trig_col" AS DOUBLE));
SIN(CAST("trig_col" AS DOUBLE));
COS(CAST("trig_col" AS DOUBLE));
TAN(CAST("trig_col" AS DOUBLE));
CASE WHEN "trig_col" = 0 THEN NULL ELSE COT(CAST("trig_col" AS DOUBLE)) END;

-- === SPARK ===
ABS(`int_col`);
ROUND(`float_col`);
CEIL(CAST(`float_col` AS DOUBLE));
FLOOR(CAST(`float_col` AS DOUBLE));
SQRT(CAST(`trig_col` AS DOUBLE));
EXP(CAST(`trig_col` AS DOUBLE));
SIN(CAST(`trig_col` AS DOUBLE));
COS(CAST(`trig_col` AS DOUBLE));
TAN(CAST(`trig_col` AS DOUBLE));
CASE WHEN `trig_col` = 0 THEN NULL ELSE COT(CAST(`trig_col` AS DOUBLE)) END;

-- === TRINO ===
ABS("int_col");
ROUND("float_col");
CEIL(CAST("float_col" AS DOUBLE));
FLOOR(CAST("float_col" AS DOUBLE));
SQRT(CAST("trig_col" AS DOUBLE));
EXP(CAST("trig_col" AS DOUBLE));
SIN(CAST("trig_col" AS DOUBLE));
COS(CAST("trig_col" AS DOUBLE));
TAN(CAST("trig_col" AS DOUBLE));
CASE
  WHEN "trig_col" = 0
  THEN NULL
  ELSE CAST(1.0 AS DOUBLE) / TAN(CAST("trig_col" AS DOUBLE))
END;
