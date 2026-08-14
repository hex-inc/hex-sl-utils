-- === CALCS ===
-- year(ts_tz)
-- quarter(ts_tz)
-- month(ts_tz)
-- day(ts_tz)
-- dayofweek(ts_tz)
-- hour(ts_tz)
-- minute(ts_tz)
-- second(ts_tz)
-- millisecond(ts_tz)

-- === BIGQUERY ===
EXTRACT(YEAR FROM DATETIME(`ts_tz`, 'America/New_York'));
EXTRACT(QUARTER FROM DATETIME(`ts_tz`, 'America/New_York'));
EXTRACT(MONTH FROM DATETIME(`ts_tz`, 'America/New_York'));
EXTRACT(DAY FROM DATETIME(`ts_tz`, 'America/New_York'));
EXTRACT(DAYOFWEEK FROM DATETIME(`ts_tz`, 'America/New_York'));
EXTRACT(HOUR FROM DATETIME(`ts_tz`, 'America/New_York'));
EXTRACT(MINUTE FROM DATETIME(`ts_tz`, 'America/New_York'));
CAST(TRUNC(EXTRACT(SECOND FROM DATETIME(`ts_tz`, 'America/New_York'))) AS INT64);
MOD(EXTRACT(MILLISECOND FROM DATETIME(`ts_tz`, 'America/New_York')), 1000);

-- === CLICKHOUSE ===
EXTRACT(YEAR FROM toTimeZone("ts_tz", 'America/New_York'));
EXTRACT(QUARTER FROM toTimeZone("ts_tz", 'America/New_York'));
EXTRACT(MONTH FROM toTimeZone("ts_tz", 'America/New_York'));
EXTRACT(DAY FROM toTimeZone("ts_tz", 'America/New_York'));
toDayOfWeek(toTimeZone("ts_tz", 'America/New_York'), 3);
EXTRACT(HOUR FROM toTimeZone("ts_tz", 'America/New_York'));
EXTRACT(MINUTE FROM toTimeZone("ts_tz", 'America/New_York'));
CAST(EXTRACT(SECOND FROM toTimeZone("ts_tz", 'America/New_York')) AS Nullable(Int32));
EXTRACT(MILLISECOND FROM toTimeZone("ts_tz", 'America/New_York')) % 1000;

-- === DUCKDB ===
EXTRACT(YEAR FROM "ts_tz" AT TIME ZONE 'America/New_York');
EXTRACT(QUARTER FROM "ts_tz" AT TIME ZONE 'America/New_York');
EXTRACT(MONTH FROM "ts_tz" AT TIME ZONE 'America/New_York');
EXTRACT(DAY FROM "ts_tz" AT TIME ZONE 'America/New_York');
EXTRACT(DAYOFWEEK FROM "ts_tz" AT TIME ZONE 'America/New_York') + 1;
EXTRACT(HOUR FROM "ts_tz" AT TIME ZONE 'America/New_York');
EXTRACT(MINUTE FROM "ts_tz" AT TIME ZONE 'America/New_York');
CAST(EXTRACT(SECOND FROM "ts_tz" AT TIME ZONE 'America/New_York') AS BIGINT);
EXTRACT('MILLISECOND' FROM "ts_tz" AT TIME ZONE 'America/New_York') % 1000;

-- === MSSQL ===
DATEPART(YEAR, [ts_tz] AT TIME ZONE 'Eastern Standard Time');
DATEPART(QUARTER, [ts_tz] AT TIME ZONE 'Eastern Standard Time');
DATEPART(MONTH, [ts_tz] AT TIME ZONE 'Eastern Standard Time');
DATEPART(DAY, [ts_tz] AT TIME ZONE 'Eastern Standard Time');
DATEPART(DW, [ts_tz] AT TIME ZONE 'Eastern Standard Time');
DATEPART(HOUR, [ts_tz] AT TIME ZONE 'Eastern Standard Time');
DATEPART(MINUTE, [ts_tz] AT TIME ZONE 'Eastern Standard Time');
CAST(DATEPART(SECOND, [ts_tz] AT TIME ZONE 'Eastern Standard Time') AS INTEGER);
DATEPART(MILLISECOND, [ts_tz] AT TIME ZONE 'Eastern Standard Time') % 1000;

-- === MYSQL ===
EXTRACT(YEAR FROM CAST(CONVERT_TZ(`ts_tz`, 'UTC', 'America/New_York') AS DATETIME(3)));
EXTRACT(QUARTER FROM CAST(CONVERT_TZ(`ts_tz`, 'UTC', 'America/New_York') AS DATETIME(3)));
EXTRACT(MONTH FROM CAST(CONVERT_TZ(`ts_tz`, 'UTC', 'America/New_York') AS DATETIME(3)));
EXTRACT(DAY FROM CAST(CONVERT_TZ(`ts_tz`, 'UTC', 'America/New_York') AS DATETIME(3)));
DAYOFWEEK(CAST(CONVERT_TZ(`ts_tz`, 'UTC', 'America/New_York') AS DATETIME(3)));
EXTRACT(HOUR FROM CAST(CONVERT_TZ(`ts_tz`, 'UTC', 'America/New_York') AS DATETIME(3)));
EXTRACT(MINUTE FROM CAST(CONVERT_TZ(`ts_tz`, 'UTC', 'America/New_York') AS DATETIME(3)));
CAST(EXTRACT(SECOND FROM CAST(CONVERT_TZ(`ts_tz`, 'UTC', 'America/New_York') AS DATETIME(3))) AS SIGNED);
FLOOR(
  EXTRACT(microsecond FROM CAST(CONVERT_TZ(`ts_tz`, 'UTC', 'America/New_York') AS DATETIME(3))) / 1000
);

-- === POSTGRES ===
EXTRACT(YEAR FROM "ts_tz" AT TIME ZONE 'America/New_York');
EXTRACT(QUARTER FROM "ts_tz" AT TIME ZONE 'America/New_York');
EXTRACT(MONTH FROM "ts_tz" AT TIME ZONE 'America/New_York');
EXTRACT(DAY FROM "ts_tz" AT TIME ZONE 'America/New_York');
EXTRACT(dow FROM "ts_tz" AT TIME ZONE 'America/New_York') + 1;
EXTRACT(HOUR FROM "ts_tz" AT TIME ZONE 'America/New_York');
EXTRACT(MINUTE FROM "ts_tz" AT TIME ZONE 'America/New_York');
CAST(FLOOR(EXTRACT('second' FROM "ts_tz" AT TIME ZONE 'America/New_York')) AS INT);
CAST(FLOOR(EXTRACT('millisecond' FROM "ts_tz")) AS INT) % 1000;

-- === REDSHIFT ===
EXTRACT(YEAR FROM "ts_tz" AT TIME ZONE 'America/New_York');
EXTRACT(QUARTER FROM "ts_tz" AT TIME ZONE 'America/New_York');
EXTRACT(MONTH FROM "ts_tz" AT TIME ZONE 'America/New_York');
EXTRACT(DAY FROM "ts_tz" AT TIME ZONE 'America/New_York');
EXTRACT(dow FROM "ts_tz" AT TIME ZONE 'America/New_York') + 1;
EXTRACT(HOUR FROM "ts_tz" AT TIME ZONE 'America/New_York');
EXTRACT(MINUTE FROM "ts_tz" AT TIME ZONE 'America/New_York');
CAST(FLOOR(EXTRACT('second' FROM "ts_tz" AT TIME ZONE 'America/New_York')) AS INTEGER);
MOD(CAST(FLOOR(EXTRACT('millisecond' FROM "ts_tz")) AS INTEGER), 1000);

-- === SNOWFLAKE ===
DATE_PART(YEAR, CONVERT_TIMEZONE('America/New_York', "ts_tz"));
DATE_PART(QUARTER, CONVERT_TIMEZONE('America/New_York', "ts_tz"));
DATE_PART(MONTH, CONVERT_TIMEZONE('America/New_York', "ts_tz"));
DATE_PART(DAY, CONVERT_TIMEZONE('America/New_York', "ts_tz"));
DATE_PART(DAYOFWEEK, CONVERT_TIMEZONE('America/New_York', "ts_tz")) + 1;
DATE_PART('hour', CONVERT_TIMEZONE('America/New_York', "ts_tz"));
DATE_PART('minute', CONVERT_TIMEZONE('America/New_York', "ts_tz"));
CAST(DATE_PART('second', CONVERT_TIMEZONE('America/New_York', "ts_tz")) AS BIGINT);
DATE_PART('epoch_millisecond', CONVERT_TIMEZONE('America/New_York', "ts_tz")) % 1000;

-- === SPARK ===
EXTRACT(YEAR FROM CAST(CONVERT_TIMEZONE('UTC', 'America/New_York', `ts_tz`) AS TIMESTAMP));
EXTRACT(QUARTER FROM CAST(CONVERT_TIMEZONE('UTC', 'America/New_York', `ts_tz`) AS TIMESTAMP));
EXTRACT(MONTH FROM CAST(CONVERT_TIMEZONE('UTC', 'America/New_York', `ts_tz`) AS TIMESTAMP));
EXTRACT(DAY FROM CAST(CONVERT_TIMEZONE('UTC', 'America/New_York', `ts_tz`) AS TIMESTAMP));
DAYOFWEEK(TO_DATE(CAST(CONVERT_TIMEZONE('UTC', 'America/New_York', `ts_tz`) AS TIMESTAMP)));
EXTRACT(HOUR FROM CAST(CONVERT_TIMEZONE('UTC', 'America/New_York', `ts_tz`) AS TIMESTAMP));
EXTRACT(MINUTE FROM CAST(CONVERT_TIMEZONE('UTC', 'America/New_York', `ts_tz`) AS TIMESTAMP));
CAST(EXTRACT(SECOND FROM CAST(CONVERT_TIMEZONE('UTC', 'America/New_York', `ts_tz`) AS TIMESTAMP)) AS BIGINT);
CAST(DATE_FORMAT(CAST(CONVERT_TIMEZONE('UTC', 'America/New_York', `ts_tz`) AS TIMESTAMP), 'SSS') AS INT);

-- === TRINO ===
EXTRACT(YEAR FROM AT_TIMEZONE("ts_tz", 'America/New_York'));
EXTRACT(QUARTER FROM AT_TIMEZONE("ts_tz", 'America/New_York'));
EXTRACT(MONTH FROM AT_TIMEZONE("ts_tz", 'America/New_York'));
EXTRACT(DAY FROM AT_TIMEZONE("ts_tz", 'America/New_York'));
DAY_OF_WEEK(AT_TIMEZONE("ts_tz", 'America/New_York')) % 7 + 1;
EXTRACT(HOUR FROM AT_TIMEZONE("ts_tz", 'America/New_York'));
EXTRACT(MINUTE FROM AT_TIMEZONE("ts_tz", 'America/New_York'));
CAST(EXTRACT(SECOND FROM AT_TIMEZONE("ts_tz", 'America/New_York')) AS BIGINT);
MILLISECOND(AT_TIMEZONE("ts_tz", 'America/New_York'));
