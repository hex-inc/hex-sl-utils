-- === CALCS ===
-- totext(int_col)
-- totext(float_col)
-- totext(bool_col)
-- totext(date_col)
-- totext(datetime_col)
-- toboolean(int_col)
-- toboolean(string_col)
-- tonumber(string_col)
-- tonumber(bool_col)
-- todate(date_string_col)
-- todatetime(ts_string_col)
-- todatetime(ts_string_col, 'UTC')
-- todatetime(ts_string_col, 'America/New_York')

-- === BIGQUERY ===
CASE
  WHEN FLOOR(`int_col`) = CEIL(`int_col`)
  AND `int_col` >= -2147483648
  AND `int_col` <= 2147483647
  THEN CAST(CAST(TRUNC(`int_col`) AS INT64) AS STRING)
  ELSE CAST(`int_col` AS STRING)
END;
CASE
  WHEN FLOOR(`float_col`) = CEIL(`float_col`)
  AND `float_col` >= -2147483648
  AND `float_col` <= 2147483647
  THEN CAST(CAST(TRUNC(`float_col`) AS INT64) AS STRING)
  ELSE CAST(`float_col` AS STRING)
END;
CASE WHEN `bool_col` THEN 'true' ELSE 'false' END;
CAST(`date_col` AS STRING);
CAST(`datetime_col` AS STRING);
`int_col` <> 0;
CASE
  WHEN LOWER(`string_col`) IN ('true', '1')
  THEN TRUE
  WHEN LOWER(`string_col`) IN ('false', '0')
  THEN FALSE
  ELSE NULL
END;
SAFE_CAST(`string_col` AS FLOAT64);
CASE WHEN `bool_col` THEN 1 ELSE 0 END;
SAFE_CAST(`date_string_col` AS DATE);
SAFE_CAST(`ts_string_col` AS DATETIME);
TIMESTAMP(SAFE_CAST(`ts_string_col` AS DATETIME), 'UTC');
TIMESTAMP(SAFE_CAST(`ts_string_col` AS DATETIME), 'America/New_York');

-- === CLICKHOUSE ===
CASE
  WHEN FLOOR("int_col") = CEIL("int_col")
  AND "int_col" >= -2147483648
  AND "int_col" <= 2147483647
  THEN CAST(CAST("int_col" AS Nullable(Int32)) AS Nullable(String))
  ELSE CAST("int_col" AS Nullable(String))
END;
CASE
  WHEN FLOOR("float_col") = CEIL("float_col")
  AND "float_col" >= -2147483648
  AND "float_col" <= 2147483647
  THEN CAST(CAST("float_col" AS Nullable(Int32)) AS Nullable(String))
  ELSE CAST("float_col" AS Nullable(String))
END;
CASE WHEN "bool_col" THEN 'true' ELSE 'false' END;
CAST("date_col" AS Nullable(String));
CAST(toDateTime("datetime_col") AS Nullable(String));
"int_col" <> 0;
CASE
  WHEN LOWER("string_col") IN ('true', '1')
  THEN TRUE
  WHEN LOWER("string_col") IN ('false', '0')
  THEN FALSE
  ELSE NULL
END;
accurateCastOrNull("string_col", 'Nullable(Float64)');
CASE WHEN "bool_col" THEN 1 ELSE 0 END;
accurateCastOrNull("date_string_col", 'Nullable(DATE)');
parseDateTime64BestEffortOrNull("ts_string_col", 3, 'America/New_York');
parseDateTime64BestEffortOrNull("ts_string_col", 3, 'UTC');
parseDateTime64BestEffortOrNull("ts_string_col", 3, 'America/New_York');

-- === DUCKDB ===
CASE
  WHEN FLOOR("int_col") = CEIL("int_col")
  AND "int_col" >= -2147483648
  AND "int_col" <= 2147483647
  THEN CAST(CAST("int_col" AS INT) AS TEXT)
  ELSE CAST("int_col" AS TEXT)
END;
CASE
  WHEN FLOOR("float_col") = CEIL("float_col")
  AND "float_col" >= -2147483648
  AND "float_col" <= 2147483647
  THEN CAST(CAST("float_col" AS INT) AS TEXT)
  ELSE CAST("float_col" AS TEXT)
END;
CASE WHEN "bool_col" THEN 'true' ELSE 'false' END;
CAST("date_col" AS TEXT);
CAST("datetime_col" AS TEXT);
"int_col" <> 0;
CASE
  WHEN LOWER("string_col") IN ('true', '1')
  THEN TRUE
  WHEN LOWER("string_col") IN ('false', '0')
  THEN FALSE
  ELSE NULL
END;
TRY_CAST("string_col" AS DOUBLE);
CASE WHEN "bool_col" THEN 1 ELSE 0 END;
TRY_CAST("date_string_col" AS DATE);
TRY_CAST(TRY_STRPTIME(
  "ts_string_col",
  [
    '%Y-%m',
    '%Y-%m-%d',
    '%Y-%m-%dT%H:%M:%S',
    '%Y-%m-%dT%H:%M:%S.%g',
    '%Y-%m-%dT%H:%M:%S.%f',
    '%Y-%m-%dT%H:%M',
    '%Y-%m-%d %H:%M:%S',
    '%Y-%m-%d %H:%M:%S.%g',
    '%Y-%m-%d %H:%M:%S.%f',
    '%Y-%m-%d %H:%M',
    '%Y-%m-%dT%H:%M:%S%z',
    '%Y-%m-%dT%H:%M:%S.%g%z',
    '%Y-%m-%dT%H:%M:%S.%f%z',
    '%Y-%m-%dT%H:%M%z',
    '%Y-%m-%d %H:%M:%S%z',
    '%Y-%m-%d %H:%M:%S.%g%z',
    '%Y-%m-%d %H:%M:%S.%f%z',
    '%Y-%m-%d %H:%M%z',
    '%m/%d/%Y',
    '%m/%d/%Y %H:%M:%S',
    '%m/%d/%Y %H:%M:%S.%g',
    '%m/%d/%Y %H:%M:%S.%f',
    '%m/%d/%Y %H:%M',
    '%b %-d %Y',
    '%b %-d %Y %H:%M:%S',
    '%b %-d %Y %H:%M:%S.%g',
    '%b %-d %Y %H:%M:%S.%f',
    '%b %-d %Y %H:%M',
    '%a %b %-d %H:%M:%S %Y',
    '%a %b %-d %H:%M:%S.%g %Y',
    '%a %b %-d %H:%M:%S.%f %Y',
    '%a %b %-d %H:%M %Y',
    '%d %b %Y',
    '%d %b %Y %H:%M:%S',
    '%d %b %Y %H:%M:%S.%g',
    '%d %b %Y %H:%M:%S.%f',
    '%d %b %Y %H:%M',
    '%a, %d %b %Y',
    '%a, %d %b %Y %H:%M:%S',
    '%a, %d %b %Y %H:%M:%S.%g',
    '%a, %d %b %Y %H:%M:%S.%f',
    '%a, %d %b %Y %H:%M',
    '%B %d, %Y',
    '%B %d, %Y %H:%M:%S',
    '%B %d, %Y %H:%M:%S.%g',
    '%B %d, %Y %H:%M:%S.%f',
    '%B %d, %Y %H:%M',
    '%Y-%m-%dT%H:%M:%S%Z'
  ]
) AS TIMESTAMP);
TRY_CAST(TRY_STRPTIME(
  "ts_string_col",
  [
    '%Y-%m',
    '%Y-%m-%d',
    '%Y-%m-%dT%H:%M:%S',
    '%Y-%m-%dT%H:%M:%S.%g',
    '%Y-%m-%dT%H:%M:%S.%f',
    '%Y-%m-%dT%H:%M',
    '%Y-%m-%d %H:%M:%S',
    '%Y-%m-%d %H:%M:%S.%g',
    '%Y-%m-%d %H:%M:%S.%f',
    '%Y-%m-%d %H:%M',
    '%Y-%m-%dT%H:%M:%S%z',
    '%Y-%m-%dT%H:%M:%S.%g%z',
    '%Y-%m-%dT%H:%M:%S.%f%z',
    '%Y-%m-%dT%H:%M%z',
    '%Y-%m-%d %H:%M:%S%z',
    '%Y-%m-%d %H:%M:%S.%g%z',
    '%Y-%m-%d %H:%M:%S.%f%z',
    '%Y-%m-%d %H:%M%z',
    '%m/%d/%Y',
    '%m/%d/%Y %H:%M:%S',
    '%m/%d/%Y %H:%M:%S.%g',
    '%m/%d/%Y %H:%M:%S.%f',
    '%m/%d/%Y %H:%M',
    '%b %-d %Y',
    '%b %-d %Y %H:%M:%S',
    '%b %-d %Y %H:%M:%S.%g',
    '%b %-d %Y %H:%M:%S.%f',
    '%b %-d %Y %H:%M',
    '%a %b %-d %H:%M:%S %Y',
    '%a %b %-d %H:%M:%S.%g %Y',
    '%a %b %-d %H:%M:%S.%f %Y',
    '%a %b %-d %H:%M %Y',
    '%d %b %Y',
    '%d %b %Y %H:%M:%S',
    '%d %b %Y %H:%M:%S.%g',
    '%d %b %Y %H:%M:%S.%f',
    '%d %b %Y %H:%M',
    '%a, %d %b %Y',
    '%a, %d %b %Y %H:%M:%S',
    '%a, %d %b %Y %H:%M:%S.%g',
    '%a, %d %b %Y %H:%M:%S.%f',
    '%a, %d %b %Y %H:%M',
    '%B %d, %Y',
    '%B %d, %Y %H:%M:%S',
    '%B %d, %Y %H:%M:%S.%g',
    '%B %d, %Y %H:%M:%S.%f',
    '%B %d, %Y %H:%M',
    '%Y-%m-%dT%H:%M:%S%Z'
  ]
) AS TIMESTAMP) AT TIME ZONE 'UTC';
TRY_CAST(TRY_STRPTIME(
  "ts_string_col",
  [
    '%Y-%m',
    '%Y-%m-%d',
    '%Y-%m-%dT%H:%M:%S',
    '%Y-%m-%dT%H:%M:%S.%g',
    '%Y-%m-%dT%H:%M:%S.%f',
    '%Y-%m-%dT%H:%M',
    '%Y-%m-%d %H:%M:%S',
    '%Y-%m-%d %H:%M:%S.%g',
    '%Y-%m-%d %H:%M:%S.%f',
    '%Y-%m-%d %H:%M',
    '%Y-%m-%dT%H:%M:%S%z',
    '%Y-%m-%dT%H:%M:%S.%g%z',
    '%Y-%m-%dT%H:%M:%S.%f%z',
    '%Y-%m-%dT%H:%M%z',
    '%Y-%m-%d %H:%M:%S%z',
    '%Y-%m-%d %H:%M:%S.%g%z',
    '%Y-%m-%d %H:%M:%S.%f%z',
    '%Y-%m-%d %H:%M%z',
    '%m/%d/%Y',
    '%m/%d/%Y %H:%M:%S',
    '%m/%d/%Y %H:%M:%S.%g',
    '%m/%d/%Y %H:%M:%S.%f',
    '%m/%d/%Y %H:%M',
    '%b %-d %Y',
    '%b %-d %Y %H:%M:%S',
    '%b %-d %Y %H:%M:%S.%g',
    '%b %-d %Y %H:%M:%S.%f',
    '%b %-d %Y %H:%M',
    '%a %b %-d %H:%M:%S %Y',
    '%a %b %-d %H:%M:%S.%g %Y',
    '%a %b %-d %H:%M:%S.%f %Y',
    '%a %b %-d %H:%M %Y',
    '%d %b %Y',
    '%d %b %Y %H:%M:%S',
    '%d %b %Y %H:%M:%S.%g',
    '%d %b %Y %H:%M:%S.%f',
    '%d %b %Y %H:%M',
    '%a, %d %b %Y',
    '%a, %d %b %Y %H:%M:%S',
    '%a, %d %b %Y %H:%M:%S.%g',
    '%a, %d %b %Y %H:%M:%S.%f',
    '%a, %d %b %Y %H:%M',
    '%B %d, %Y',
    '%B %d, %Y %H:%M:%S',
    '%B %d, %Y %H:%M:%S.%g',
    '%B %d, %Y %H:%M:%S.%f',
    '%B %d, %Y %H:%M',
    '%Y-%m-%dT%H:%M:%S%Z'
  ]
) AS TIMESTAMP) AT TIME ZONE 'America/New_York';

-- === MSSQL ===
CASE
  WHEN FLOOR([int_col]) = CEILING([int_col])
  AND [int_col] >= -2147483648
  AND [int_col] <= 2147483647
  THEN CAST(CAST([int_col] AS INTEGER) AS VARCHAR(MAX))
  ELSE CAST([int_col] AS VARCHAR(MAX))
END;
CASE
  WHEN FLOOR([float_col]) = CEILING([float_col])
  AND [float_col] >= -2147483648
  AND [float_col] <= 2147483647
  THEN CAST(CAST([float_col] AS INTEGER) AS VARCHAR(MAX))
  ELSE CAST([float_col] AS VARCHAR(MAX))
END;
CASE WHEN [bool_col] <> 0 THEN 'true' ELSE 'false' END;
CAST([date_col] AS VARCHAR(MAX));
REPLACE(CAST([datetime_col] AS VARCHAR), '.000000', '');
IIF([int_col] <> 0, 1, 0);
IIF(
  CASE
    WHEN LOWER([string_col]) IN ('true', '1')
    THEN 1
    WHEN LOWER([string_col]) IN ('false', '0')
    THEN 0
    ELSE NULL
  END <> 0,
  1,
  0
);
TRY_CAST([string_col] AS FLOAT);
CASE WHEN [bool_col] <> 0 THEN 1 ELSE 0 END;
TRY_CAST([date_string_col] AS DATE);
TRY_CAST([ts_string_col] AS DATETIME2);
TRY_CAST([ts_string_col] AS DATETIME2) AT TIME ZONE 'UTC';
TRY_CAST([ts_string_col] AS DATETIME2) AT TIME ZONE 'Eastern Standard Time';

-- === MYSQL ===
CASE
  WHEN FLOOR(`int_col`) = CEIL(`int_col`)
  AND `int_col` >= -2147483648
  AND `int_col` <= 2147483647
  THEN CAST(CAST(`int_col` AS SIGNED) AS CHAR)
  ELSE CAST(`int_col` AS CHAR)
END;
CASE
  WHEN FLOOR(`float_col`) = CEIL(`float_col`)
  AND `float_col` >= -2147483648
  AND `float_col` <= 2147483647
  THEN CAST(CAST(`float_col` AS SIGNED) AS CHAR)
  ELSE CAST(`float_col` AS CHAR)
END;
CASE WHEN `bool_col` THEN 'true' ELSE 'false' END;
CAST(`date_col` AS CHAR);
CAST(`datetime_col` AS CHAR);
`int_col` <> 0;
CASE
  WHEN LOWER(`string_col`) IN ('true', '1')
  THEN TRUE
  WHEN LOWER(`string_col`) IN ('false', '0')
  THEN FALSE
  ELSE NULL
END;
CASE
  WHEN (`string_col` RLIKE '^[-+]?[0-9]*\\.?[0-9]+$')
  THEN CAST(`string_col` AS DOUBLE)
  ELSE NULL
END;
CASE WHEN `bool_col` THEN 1 ELSE 0 END;
CAST(`date_string_col` AS DATE);
CAST(`ts_string_col` AS DATETIME(3));
CAST(CONVERT_TZ(CAST(`ts_string_col` AS DATETIME(3)), 'UTC', 'UTC') AS DATETIME);
CAST(CONVERT_TZ(CAST(`ts_string_col` AS DATETIME(3)), 'America/New_York', 'UTC') AS DATETIME);

-- === POSTGRES ===
CASE
  WHEN FLOOR("int_col") = CEIL("int_col")
  AND "int_col" >= -2147483648
  AND "int_col" <= 2147483647
  THEN CAST(CAST("int_col" AS INT) AS VARCHAR)
  ELSE CAST("int_col" AS VARCHAR)
END;
CASE
  WHEN FLOOR("float_col") = CEIL("float_col")
  AND "float_col" >= -2147483648
  AND "float_col" <= 2147483647
  THEN CAST(CAST("float_col" AS INT) AS VARCHAR)
  ELSE CAST("float_col" AS VARCHAR)
END;
CASE WHEN "bool_col" THEN 'true' ELSE 'false' END;
CAST("date_col" AS VARCHAR);
CAST("datetime_col" AS VARCHAR);
"int_col" <> 0;
CASE
  WHEN LOWER("string_col") IN ('true', '1')
  THEN TRUE
  WHEN LOWER("string_col") IN ('false', '0')
  THEN FALSE
  ELSE NULL
END;
CASE
  WHEN "string_col" ~ '^[-+]?[0-9]*\.?[0-9]+$'
  THEN CAST("string_col" AS DOUBLE PRECISION)
  ELSE NULL
END;
CASE WHEN "bool_col" THEN 1 ELSE 0 END;
CASE
  WHEN "date_string_col" ~ '^\d{4}-\d{2}-\d{2}$'
  THEN CAST("date_string_col" AS DATE)
  ELSE NULL
END;
CAST("ts_string_col" AS TIMESTAMP);
CAST("ts_string_col" AS TIMESTAMP) AT TIME ZONE 'UTC';
CAST("ts_string_col" AS TIMESTAMP) AT TIME ZONE 'America/New_York';

-- === REDSHIFT ===
CASE
  WHEN FLOOR("int_col") = CEIL("int_col")
  AND "int_col" >= -2147483648
  AND "int_col" <= 2147483647
  THEN CAST(CAST("int_col" AS INTEGER) AS VARCHAR)
  ELSE CAST("int_col" AS VARCHAR)
END;
CASE
  WHEN FLOOR("float_col") = CEIL("float_col")
  AND "float_col" >= -2147483648
  AND "float_col" <= 2147483647
  THEN CAST(CAST("float_col" AS INTEGER) AS VARCHAR)
  ELSE CAST("float_col" AS VARCHAR)
END;
CASE
  WHEN "bool_col"
  THEN CAST('true' AS VARCHAR(MAX))
  ELSE CAST('false' AS VARCHAR(MAX))
END;
CAST("date_col" AS VARCHAR);
CAST("datetime_col" AS VARCHAR);
"int_col" <> 0;
CASE
  WHEN LOWER("string_col") IN ('true', '1')
  THEN TRUE
  WHEN LOWER("string_col") IN ('false', '0')
  THEN FALSE
  ELSE NULL
END;
CASE
  WHEN "string_col" ~ '^[-+]?[0-9]*\\.?[0-9]+$'
  THEN CAST("string_col" AS DOUBLE PRECISION)
  ELSE NULL
END;
CASE WHEN "bool_col" THEN 1 ELSE 0 END;
CASE
  WHEN "date_string_col" ~ '^\\d{4}-\\d{2}-\\d{2}$'
  THEN CAST("date_string_col" AS DATE)
  ELSE NULL
END;
CAST("ts_string_col" AS TIMESTAMP);
CAST("ts_string_col" AS TIMESTAMP) AT TIME ZONE 'UTC';
CAST("ts_string_col" AS TIMESTAMP) AT TIME ZONE 'America/New_York';

-- === SNOWFLAKE ===
CASE
  WHEN FLOOR("int_col") = CEIL("int_col")
  AND "int_col" >= -2147483648
  AND "int_col" <= 2147483647
  THEN CAST(CAST("int_col" AS INT) AS VARCHAR)
  ELSE CAST("int_col" AS VARCHAR)
END;
CASE
  WHEN FLOOR("float_col") = CEIL("float_col")
  AND "float_col" >= -2147483648
  AND "float_col" <= 2147483647
  THEN CAST(CAST("float_col" AS INT) AS VARCHAR)
  ELSE CAST("float_col" AS VARCHAR)
END;
CASE WHEN "bool_col" THEN 'true' ELSE 'false' END;
CAST("date_col" AS VARCHAR);
REPLACE(CAST("datetime_col" AS VARCHAR), '.000', '');
"int_col" <> 0;
CASE
  WHEN LOWER("string_col") IN ('true', '1')
  THEN TRUE
  WHEN LOWER("string_col") IN ('false', '0')
  THEN FALSE
  ELSE NULL
END;
TRY_CAST("string_col" AS DOUBLE);
CASE WHEN "bool_col" THEN 1 ELSE 0 END;
TRY_CAST("date_string_col" AS DATE);
TRY_CAST("ts_string_col" AS TIMESTAMP);
TO_TIMESTAMP_TZ(
  CONCAT(
    TO_CHAR(TRY_CAST("ts_string_col" AS TIMESTAMP), 'YYYY-MM-DD HH24:MI:SS.FF6'),
    ' +00'
  )
);
CONVERT_TIMEZONE(
  'America/New_York',
  TO_TIMESTAMP_TZ(
    CONCAT(
      TO_CHAR(
        CONVERT_TIMEZONE('America/New_York', 'UTC', TRY_CAST("ts_string_col" AS TIMESTAMP)),
        'YYYY-MM-DD HH24:MI:SS.FF6'
      ),
      ' +00'
    )
  )
);

-- === SPARK ===
CASE
  WHEN FLOOR(`int_col`) = CEIL(`int_col`)
  AND `int_col` >= -2147483648
  AND `int_col` <= 2147483647
  THEN CAST(CAST(`int_col` AS INT) AS STRING)
  ELSE CAST(`int_col` AS STRING)
END;
CASE
  WHEN FLOOR(`float_col`) = CEIL(`float_col`)
  AND `float_col` >= -2147483648
  AND `float_col` <= 2147483647
  THEN CAST(CAST(`float_col` AS INT) AS STRING)
  ELSE CAST(`float_col` AS STRING)
END;
CASE WHEN `bool_col` THEN 'true' ELSE 'false' END;
CAST(`date_col` AS STRING);
CAST(`datetime_col` AS STRING);
`int_col` <> 0;
CASE
  WHEN LOWER(`string_col`) IN ('true', '1')
  THEN TRUE
  WHEN LOWER(`string_col`) IN ('false', '0')
  THEN FALSE
  ELSE NULL
END;
CAST(`string_col` AS DOUBLE);
CASE WHEN `bool_col` THEN 1 ELSE 0 END;
CAST(`date_string_col` AS DATE);
CAST(`ts_string_col` AS TIMESTAMP);
CAST(CONVERT_TIMEZONE('UTC', 'UTC', CAST(`ts_string_col` AS TIMESTAMP)) AS TIMESTAMP);
CAST(CONVERT_TIMEZONE('America/New_York', 'UTC', CAST(`ts_string_col` AS TIMESTAMP)) AS TIMESTAMP);

-- === TRINO ===
CASE
  WHEN FLOOR("int_col") = CEIL("int_col")
  AND "int_col" >= -2147483648
  AND "int_col" <= 2147483647
  THEN CAST(CAST("int_col" AS INTEGER) AS VARCHAR)
  ELSE CAST("int_col" AS VARCHAR)
END;
CASE
  WHEN FLOOR("float_col") = CEIL("float_col")
  AND "float_col" >= -2147483648
  AND "float_col" <= 2147483647
  THEN CAST(CAST("float_col" AS INTEGER) AS VARCHAR)
  ELSE CAST("float_col" AS VARCHAR)
END;
CASE WHEN "bool_col" THEN 'true' ELSE 'false' END;
CAST("date_col" AS VARCHAR);
REPLACE(CAST("datetime_col" AS VARCHAR), '.000', '');
"int_col" <> 0;
CASE
  WHEN LOWER("string_col") IN ('true', '1')
  THEN TRUE
  WHEN LOWER("string_col") IN ('false', '0')
  THEN FALSE
  ELSE NULL
END;
TRY_CAST("string_col" AS DOUBLE);
CASE WHEN "bool_col" THEN 1 ELSE 0 END;
TRY_CAST("date_string_col" AS DATE);
TRY_CAST("ts_string_col" AS TIMESTAMP);
WITH_TIMEZONE(TRY_CAST("ts_string_col" AS TIMESTAMP), 'UTC');
WITH_TIMEZONE(TRY_CAST("ts_string_col" AS TIMESTAMP), 'America/New_York');
