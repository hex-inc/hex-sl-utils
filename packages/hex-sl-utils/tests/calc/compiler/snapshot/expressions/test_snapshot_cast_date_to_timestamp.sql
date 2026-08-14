-- === CALCS ===
-- todatetime(date_col)
-- todatetime(date_col, 'America/New_York')

-- === BIGQUERY ===
CAST(`date_col` AS DATETIME);
TIMESTAMP(CAST(`date_col` AS DATETIME), 'America/New_York');

-- === CLICKHOUSE ===
toDateTime64("date_col", 3);
toDateTime64("date_col", 3, 'America/New_York');

-- === DUCKDB ===
CAST("date_col" AS TIMESTAMP);
CAST("date_col" AS TIMESTAMP) AT TIME ZONE 'America/New_York';

-- === MSSQL ===
CAST([date_col] AS DATETIME2);
CAST([date_col] AS DATETIME2) AT TIME ZONE 'Eastern Standard Time';

-- === MYSQL ===
CAST(`date_col` AS DATETIME);
CAST(CONVERT_TZ(CAST(`date_col` AS DATETIME), 'America/New_York', 'UTC') AS DATETIME);

-- === POSTGRES ===
CAST("date_col" AS TIMESTAMP);
CAST("date_col" AS TIMESTAMP) AT TIME ZONE 'America/New_York';

-- === REDSHIFT ===
CAST("date_col" AS TIMESTAMP);
CAST("date_col" AS TIMESTAMP) AT TIME ZONE 'America/New_York';

-- === SNOWFLAKE ===
CAST("date_col" AS TIMESTAMP);
CONVERT_TIMEZONE(
  'America/New_York',
  TO_TIMESTAMP_TZ(
    CONCAT(
      TO_CHAR(
        CONVERT_TIMEZONE('America/New_York', 'UTC', CAST("date_col" AS TIMESTAMP)),
        'YYYY-MM-DD HH24:MI:SS.FF6'
      ),
      'Z'
    )
  )
);

-- === SPARK ===
CAST(`date_col` AS TIMESTAMP);
CAST(CONVERT_TIMEZONE('America/New_York', 'UTC', CAST(`date_col` AS TIMESTAMP)) AS TIMESTAMP);

-- === TRINO ===
CAST("date_col" AS TIMESTAMP);
WITH_TIMEZONE(CAST("date_col" AS TIMESTAMP), 'America/New_York');
