-- === CALCS ===
-- todate(tstz_col)
-- todate(ts_col)

-- === BIGQUERY ===
CAST(DATETIME(`tstz_col`, 'America/New_York') AS DATE);
CAST(`ts_col` AS DATE);

-- === CLICKHOUSE ===
CAST(toTimeZone("tstz_col", 'America/New_York') AS Nullable(DATE));
CAST("ts_col" AS Nullable(DATE));

-- === DUCKDB ===
CAST("tstz_col" AT TIME ZONE 'America/New_York' AS DATE);
CAST("ts_col" AS DATE);

-- === MSSQL ===
CAST([tstz_col] AT TIME ZONE 'Eastern Standard Time' AS DATE);
CAST([ts_col] AS DATE);

-- === MYSQL ===
CAST(CAST(CONVERT_TZ(`tstz_col`, 'UTC', 'America/New_York') AS DATETIME(3)) AS DATE);
CAST(`ts_col` AS DATE);

-- === POSTGRES ===
CAST("tstz_col" AT TIME ZONE 'America/New_York' AS DATE);
CAST("ts_col" AS DATE);

-- === REDSHIFT ===
CAST("tstz_col" AT TIME ZONE 'America/New_York' AS DATE);
CAST("ts_col" AS DATE);

-- === SNOWFLAKE ===
CAST(CONVERT_TIMEZONE('America/New_York', "tstz_col") AS DATE);
CAST("ts_col" AS DATE);

-- === SPARK ===
CAST(CAST(CONVERT_TIMEZONE('UTC', 'America/New_York', `tstz_col`) AS TIMESTAMP) AS DATE);
CAST(`ts_col` AS DATE);

-- === TRINO ===
CAST(AT_TIMEZONE("tstz_col", 'America/New_York') AS DATE);
CAST("ts_col" AS DATE);
