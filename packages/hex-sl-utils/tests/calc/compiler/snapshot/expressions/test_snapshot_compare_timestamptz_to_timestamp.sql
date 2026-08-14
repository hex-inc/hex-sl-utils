-- === CALCS ===
-- toNumber(tstz_col < ToDatetime('2021-01-02 10:00:00'))
-- toNumber(tstz_col < ToDate('2021-01-02'))

-- === BIGQUERY ===
CASE
  WHEN `tstz_col` < TIMESTAMP(SAFE_CAST('2021-01-02 10:00:00' AS DATETIME), 'America/New_York')
  THEN 1
  ELSE 0
END;
CASE
  WHEN `tstz_col` < TIMESTAMP(CAST(SAFE_CAST('2021-01-02' AS DATE) AS DATETIME), 'America/New_York')
  THEN 1
  ELSE 0
END;

-- === CLICKHOUSE ===
CASE
  WHEN "tstz_col" < parseDateTime64BestEffortOrNull('2021-01-02 10:00:00', 3, 'America/New_York')
  THEN 1
  ELSE 0
END;
CASE
  WHEN "tstz_col" < toDateTime64(accurateCastOrNull('2021-01-02', 'Nullable(DATE)'), 3, 'America/New_York')
  THEN 1
  ELSE 0
END;

-- === DUCKDB ===
CASE
  WHEN "tstz_col" < TRY_CAST(TRY_STRPTIME(
    '2021-01-02 10:00:00',
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
  ) AS TIMESTAMP) AT TIME ZONE 'America/New_York'
  THEN 1
  ELSE 0
END;
CASE
  WHEN "tstz_col" < CAST(TRY_CAST('2021-01-02' AS DATE) AS TIMESTAMP) AT TIME ZONE 'America/New_York'
  THEN 1
  ELSE 0
END;

-- === MSSQL ===
CASE
  WHEN [tstz_col] < TRY_CAST('2021-01-02 10:00:00' AS DATETIME2) AT TIME ZONE 'Eastern Standard Time'
  THEN 1
  ELSE 0
END;
CASE
  WHEN [tstz_col] < CAST(TRY_CAST('2021-01-02' AS DATE) AS DATETIME2) AT TIME ZONE 'Eastern Standard Time'
  THEN 1
  ELSE 0
END;

-- === MYSQL ===
CASE
  WHEN `tstz_col` < CAST(CONVERT_TZ(CAST('2021-01-02 10:00:00' AS DATETIME(3)), 'America/New_York', 'UTC') AS DATETIME)
  THEN 1
  ELSE 0
END;
CASE
  WHEN `tstz_col` < CAST(CONVERT_TZ(CAST(CAST('2021-01-02' AS DATE) AS DATETIME), 'America/New_York', 'UTC') AS DATETIME)
  THEN 1
  ELSE 0
END;

-- === POSTGRES ===
CASE
  WHEN "tstz_col" < CAST('2021-01-02 10:00:00' AS TIMESTAMP) AT TIME ZONE 'America/New_York'
  THEN 1
  ELSE 0
END;
CASE
  WHEN "tstz_col" < CAST(CASE
    WHEN '2021-01-02' ~ '^\d{4}-\d{2}-\d{2}$'
    THEN CAST('2021-01-02' AS DATE)
    ELSE NULL
  END AS TIMESTAMP) AT TIME ZONE 'America/New_York'
  THEN 1
  ELSE 0
END;

-- === REDSHIFT ===
CASE
  WHEN "tstz_col" < CAST(CAST('2021-01-02 10:00:00' AS VARCHAR(MAX)) AS TIMESTAMP) AT TIME ZONE 'America/New_York'
  THEN 1
  ELSE 0
END;
CASE
  WHEN "tstz_col" < CAST(CASE
    WHEN CAST('2021-01-02' AS VARCHAR(MAX)) ~ '^\\d{4}-\\d{2}-\\d{2}$'
    THEN CAST(CAST('2021-01-02' AS VARCHAR(MAX)) AS DATE)
    ELSE NULL
  END AS TIMESTAMP) AT TIME ZONE 'America/New_York'
  THEN 1
  ELSE 0
END;

-- === SNOWFLAKE ===
CASE
  WHEN "tstz_col" < CONVERT_TIMEZONE(
    'America/New_York',
    TO_TIMESTAMP_TZ(
      CONCAT(
        TO_CHAR(
          CONVERT_TIMEZONE('America/New_York', 'UTC', CAST('2021-01-02 10:00:00.000000' AS TIMESTAMP)),
          'YYYY-MM-DD HH24:MI:SS.FF6'
        ),
        'Z'
      )
    )
  )
  THEN 1
  ELSE 0
END;
CASE
  WHEN "tstz_col" < CONVERT_TIMEZONE(
    'America/New_York',
    TO_TIMESTAMP_TZ(
      CONCAT(
        TO_CHAR(
          CONVERT_TIMEZONE('America/New_York', 'UTC', CAST(TRY_CAST('2021-01-02' AS DATE) AS TIMESTAMP)),
          'YYYY-MM-DD HH24:MI:SS.FF6'
        ),
        'Z'
      )
    )
  )
  THEN 1
  ELSE 0
END;

-- === SPARK ===
CASE
  WHEN `tstz_col` < CAST(CONVERT_TIMEZONE('America/New_York', 'UTC', CAST('2021-01-02 10:00:00' AS TIMESTAMP)) AS TIMESTAMP)
  THEN 1
  ELSE 0
END;
CASE
  WHEN `tstz_col` < CAST(CONVERT_TIMEZONE('America/New_York', 'UTC', CAST(CAST('2021-01-02' AS DATE) AS TIMESTAMP)) AS TIMESTAMP)
  THEN 1
  ELSE 0
END;

-- === TRINO ===
CASE
  WHEN "tstz_col" < WITH_TIMEZONE(TRY_CAST('2021-01-02 10:00:00' AS TIMESTAMP), 'America/New_York')
  THEN 1
  ELSE 0
END;
CASE
  WHEN "tstz_col" < WITH_TIMEZONE(CAST(TRY_CAST('2021-01-02' AS DATE) AS TIMESTAMP), 'America/New_York')
  THEN 1
  ELSE 0
END;
