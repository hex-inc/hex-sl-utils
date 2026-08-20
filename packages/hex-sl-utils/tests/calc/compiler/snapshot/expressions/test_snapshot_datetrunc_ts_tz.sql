-- === CALCS ===
-- ts_tz
-- truncyear(ts_tz)
-- truncquarter(ts_tz)
-- truncmonth(ts_tz)
-- truncweek(ts_tz)
-- truncweekmonday(ts_tz)
-- truncday(ts_tz)
-- trunchour(ts_tz)
-- truncminute(ts_tz)
-- truncsecond(ts_tz)
-- truncmillisecond(ts_tz)

-- === BIGQUERY ===
`ts_tz`;
TIMESTAMP_TRUNC(`ts_tz`, YEAR, 'America/New_York');
TIMESTAMP_TRUNC(`ts_tz`, QUARTER, 'America/New_York');
TIMESTAMP_TRUNC(`ts_tz`, MONTH, 'America/New_York');
TIMESTAMP_TRUNC(`ts_tz`, WEEK, 'America/New_York');
TIMESTAMP_TRUNC(`ts_tz`, WEEK(MONDAY), 'America/New_York');
TIMESTAMP_TRUNC(`ts_tz`, DAY, 'America/New_York');
TIMESTAMP_TRUNC(`ts_tz`, HOUR, 'America/New_York');
TIMESTAMP_TRUNC(`ts_tz`, MINUTE, 'America/New_York');
TIMESTAMP_TRUNC(`ts_tz`, SECOND, 'America/New_York');
TIMESTAMP_TRUNC(`ts_tz`, MILLISECOND, 'America/New_York');

-- === CLICKHOUSE ===
"ts_tz";
toDateTime64(dateTrunc('year', "ts_tz", 'America/New_York'), 3, 'America/New_York');
toDateTime64(dateTrunc('quarter', "ts_tz", 'America/New_York'), 3, 'America/New_York');
toDateTime64(dateTrunc('month', "ts_tz", 'America/New_York'), 3, 'America/New_York');
toDateTime64(
  dateTrunc('week', "ts_tz" + INTERVAL 1 day, 'America/New_York') - INTERVAL 1 day,
  3,
  'America/New_York'
);
toDateTime64(dateTrunc('week', "ts_tz", 'America/New_York'), 3, 'America/New_York');
toDateTime64(dateTrunc('day', "ts_tz", 'America/New_York'), 3, 'America/New_York');
dateTrunc('hour', "ts_tz", 'America/New_York');
dateTrunc('minute', "ts_tz", 'America/New_York');
dateTrunc('second', "ts_tz", 'America/New_York');
dateTrunc('millisecond', "ts_tz", 'America/New_York');

-- === DUCKDB ===
"ts_tz";
DATE_TRUNC('YEAR', "ts_tz" AT TIME ZONE 'America/New_York') AT TIME ZONE 'America/New_York';
DATE_TRUNC('QUARTER', "ts_tz" AT TIME ZONE 'America/New_York') AT TIME ZONE 'America/New_York';
DATE_TRUNC('MONTH', "ts_tz" AT TIME ZONE 'America/New_York') AT TIME ZONE 'America/New_York';
(
  DATE_TRUNC('WEEK', (
    "ts_tz" + INTERVAL 1 day
  ) AT TIME ZONE 'America/New_York') - INTERVAL 1 day
) AT TIME ZONE 'America/New_York';
DATE_TRUNC('WEEK', "ts_tz" AT TIME ZONE 'America/New_York') AT TIME ZONE 'America/New_York';
DATE_TRUNC('DAY', "ts_tz" AT TIME ZONE 'America/New_York') AT TIME ZONE 'America/New_York';
DATE_TRUNC('HOUR', "ts_tz" AT TIME ZONE 'America/New_York') AT TIME ZONE 'America/New_York';
DATE_TRUNC('MINUTE', "ts_tz" AT TIME ZONE 'America/New_York') AT TIME ZONE 'America/New_York';
DATE_TRUNC('SECOND', "ts_tz" AT TIME ZONE 'America/New_York') AT TIME ZONE 'America/New_York';
DATE_TRUNC('MILLISECOND', "ts_tz" AT TIME ZONE 'America/New_York') AT TIME ZONE 'America/New_York';

-- === MSSQL ===
[ts_tz];
DATETIME2FROMPARTS(DATEPART(year, [ts_tz] AT TIME ZONE 'Eastern Standard Time'), 1, 1, 0, 0, 0, 0, 3) AT TIME ZONE 'Eastern Standard Time';
DATETIME2FROMPARTS(
  DATEPART(year, [ts_tz] AT TIME ZONE 'Eastern Standard Time'),
  FLOOR(
    CAST((
      DATEPART(month, [ts_tz] AT TIME ZONE 'Eastern Standard Time') - 1
    ) AS FLOAT) / 3
  ) * 3 + 1,
  1,
  0,
  0,
  0,
  0,
  3
) AT TIME ZONE 'Eastern Standard Time';
DATETIME2FROMPARTS(
  DATEPART(year, [ts_tz] AT TIME ZONE 'Eastern Standard Time'),
  DATEPART(month, [ts_tz] AT TIME ZONE 'Eastern Standard Time'),
  1,
  0,
  0,
  0,
  0,
  3
) AT TIME ZONE 'Eastern Standard Time';
DATEADD(
  DAY,
  -DATEPART(weekday, [ts_tz] AT TIME ZONE 'Eastern Standard Time') + 1,
  DATETIME2FROMPARTS(
    DATEPART(year, [ts_tz] AT TIME ZONE 'Eastern Standard Time'),
    DATEPART(month, [ts_tz] AT TIME ZONE 'Eastern Standard Time'),
    DATEPART(day, [ts_tz] AT TIME ZONE 'Eastern Standard Time'),
    0,
    0,
    0,
    0,
    3
  )
) AT TIME ZONE 'Eastern Standard Time';
DATEADD(
  DAY,
  -(
    (
      (
        DATEPART(weekday, [ts_tz] AT TIME ZONE 'Eastern Standard Time') + 5
      ) % 7
    ) + 1
  ) + 1,
  DATETIME2FROMPARTS(
    DATEPART(year, [ts_tz] AT TIME ZONE 'Eastern Standard Time'),
    DATEPART(month, [ts_tz] AT TIME ZONE 'Eastern Standard Time'),
    DATEPART(day, [ts_tz] AT TIME ZONE 'Eastern Standard Time'),
    0,
    0,
    0,
    0,
    3
  )
) AT TIME ZONE 'Eastern Standard Time';
DATETIME2FROMPARTS(
  DATEPART(year, [ts_tz] AT TIME ZONE 'Eastern Standard Time'),
  DATEPART(month, [ts_tz] AT TIME ZONE 'Eastern Standard Time'),
  DATEPART(day, [ts_tz] AT TIME ZONE 'Eastern Standard Time'),
  0,
  0,
  0,
  0,
  3
) AT TIME ZONE 'Eastern Standard Time';
DATETIME2FROMPARTS(
  DATEPART(year, [ts_tz] AT TIME ZONE 'Eastern Standard Time'),
  DATEPART(month, [ts_tz] AT TIME ZONE 'Eastern Standard Time'),
  DATEPART(day, [ts_tz] AT TIME ZONE 'Eastern Standard Time'),
  DATEPART(hour, [ts_tz] AT TIME ZONE 'Eastern Standard Time'),
  0,
  0,
  0,
  3
) AT TIME ZONE 'Eastern Standard Time';
DATETIME2FROMPARTS(
  DATEPART(year, [ts_tz] AT TIME ZONE 'Eastern Standard Time'),
  DATEPART(month, [ts_tz] AT TIME ZONE 'Eastern Standard Time'),
  DATEPART(day, [ts_tz] AT TIME ZONE 'Eastern Standard Time'),
  DATEPART(hour, [ts_tz] AT TIME ZONE 'Eastern Standard Time'),
  DATEPART(minute, [ts_tz] AT TIME ZONE 'Eastern Standard Time'),
  0,
  0,
  3
) AT TIME ZONE 'Eastern Standard Time';
DATETIME2FROMPARTS(
  DATEPART(year, [ts_tz] AT TIME ZONE 'Eastern Standard Time'),
  DATEPART(month, [ts_tz] AT TIME ZONE 'Eastern Standard Time'),
  DATEPART(day, [ts_tz] AT TIME ZONE 'Eastern Standard Time'),
  DATEPART(hour, [ts_tz] AT TIME ZONE 'Eastern Standard Time'),
  DATEPART(minute, [ts_tz] AT TIME ZONE 'Eastern Standard Time'),
  DATEPART(second, [ts_tz] AT TIME ZONE 'Eastern Standard Time'),
  0,
  3
) AT TIME ZONE 'Eastern Standard Time';
DATETIME2FROMPARTS(
  DATEPART(year, [ts_tz] AT TIME ZONE 'Eastern Standard Time'),
  DATEPART(month, [ts_tz] AT TIME ZONE 'Eastern Standard Time'),
  DATEPART(day, [ts_tz] AT TIME ZONE 'Eastern Standard Time'),
  DATEPART(hour, [ts_tz] AT TIME ZONE 'Eastern Standard Time'),
  DATEPART(minute, [ts_tz] AT TIME ZONE 'Eastern Standard Time'),
  DATEPART(second, [ts_tz] AT TIME ZONE 'Eastern Standard Time'),
  DATEPART(millisecond, [ts_tz] AT TIME ZONE 'Eastern Standard Time'),
  3
) AT TIME ZONE 'Eastern Standard Time';

-- === MYSQL ===
`ts_tz`;
CONVERT_TZ(
  CAST(DATE_FORMAT(CONVERT_TZ(`ts_tz`, 'UTC', 'America/New_York'), '%Y-01-01') AS DATE),
  'America/New_York',
  'UTC'
);
CONVERT_TZ(
  CAST(DATE_FORMAT(
    CONVERT_TZ(`ts_tz`, 'UTC', 'America/New_York'),
    CONCAT(
      '%Y-',
      (
        (
          QUARTER(CONVERT_TZ(`ts_tz`, 'UTC', 'America/New_York')) - 1
        ) * 3 + 1
      ),
      '-01'
    )
  ) AS DATE),
  'America/New_York',
  'UTC'
);
CONVERT_TZ(
  CAST(DATE_FORMAT(CONVERT_TZ(`ts_tz`, 'UTC', 'America/New_York'), '%Y-%m-01') AS DATE),
  'America/New_York',
  'UTC'
);
CONVERT_TZ(
  DATE_SUB(
    CAST(DATE_FORMAT(
      CONVERT_TZ(CONVERT_TZ(`ts_tz`, 'UTC', 'America/New_York'), 'UTC', 'America/New_York'),
      '%Y-%m-%d'
    ) AS DATE),
    INTERVAL (DAYOFWEEK(DATE(CONVERT_TZ(`ts_tz`, 'UTC', 'America/New_York'))) - 1) DAY
  ),
  'America/New_York',
  'UTC'
);
CONVERT_TZ(
  DATE_SUB(
    CAST(DATE_FORMAT(
      CONVERT_TZ(CONVERT_TZ(`ts_tz`, 'UTC', 'America/New_York'), 'UTC', 'America/New_York'),
      '%Y-%m-%d'
    ) AS DATE),
    INTERVAL (WEEKDAY(DATE(CONVERT_TZ(`ts_tz`, 'UTC', 'America/New_York')))) DAY
  ),
  'America/New_York',
  'UTC'
);
CONVERT_TZ(
  CAST(DATE_FORMAT(CONVERT_TZ(`ts_tz`, 'UTC', 'America/New_York'), '%Y-%m-%d') AS DATE),
  'America/New_York',
  'UTC'
);
CONVERT_TZ(
  CAST(DATE_FORMAT(CONVERT_TZ(`ts_tz`, 'UTC', 'America/New_York'), '%Y-%m-%d %H:00:00') AS DATETIME),
  'America/New_York',
  'UTC'
);
CONVERT_TZ(
  CAST(DATE_FORMAT(CONVERT_TZ(`ts_tz`, 'UTC', 'America/New_York'), '%Y-%m-%d %H:%i:00') AS DATETIME),
  'America/New_York',
  'UTC'
);
CONVERT_TZ(
  CAST(DATE_FORMAT(CONVERT_TZ(`ts_tz`, 'UTC', 'America/New_York'), '%Y-%m-%d %T') AS DATETIME),
  'America/New_York',
  'UTC'
);
CONVERT_TZ(
  CAST(DATE_FORMAT(CONVERT_TZ(`ts_tz`, 'UTC', 'America/New_York'), '%Y-%m-%d %T.%f') AS DATETIME(3)),
  'America/New_York',
  'UTC'
);

-- === POSTGRES ===
"ts_tz";
DATE_TRUNC('YEAR', "ts_tz" AT TIME ZONE 'America/New_York') AT TIME ZONE 'America/New_York';
DATE_TRUNC('QUARTER', "ts_tz" AT TIME ZONE 'America/New_York') AT TIME ZONE 'America/New_York';
DATE_TRUNC('MONTH', "ts_tz" AT TIME ZONE 'America/New_York') AT TIME ZONE 'America/New_York';
(
  DATE_TRUNC('WEEK', (
    "ts_tz" + INTERVAL '1 day'
  ) AT TIME ZONE 'America/New_York') - INTERVAL '1 day'
) AT TIME ZONE 'America/New_York';
DATE_TRUNC('WEEK', "ts_tz" AT TIME ZONE 'America/New_York') AT TIME ZONE 'America/New_York';
DATE_TRUNC('DAY', "ts_tz" AT TIME ZONE 'America/New_York') AT TIME ZONE 'America/New_York';
DATE_TRUNC('HOUR', "ts_tz" AT TIME ZONE 'America/New_York') AT TIME ZONE 'America/New_York';
DATE_TRUNC('MINUTE', "ts_tz" AT TIME ZONE 'America/New_York') AT TIME ZONE 'America/New_York';
DATE_TRUNC('SECOND', "ts_tz" AT TIME ZONE 'America/New_York') AT TIME ZONE 'America/New_York';
DATE_TRUNC('MILLISECOND', "ts_tz" AT TIME ZONE 'America/New_York') AT TIME ZONE 'America/New_York';

-- === REDSHIFT ===
"ts_tz";
DATE_TRUNC('YEAR', "ts_tz" AT TIME ZONE 'America/New_York') AT TIME ZONE 'America/New_York';
DATE_TRUNC('QUARTER', "ts_tz" AT TIME ZONE 'America/New_York') AT TIME ZONE 'America/New_York';
DATE_TRUNC('MONTH', "ts_tz" AT TIME ZONE 'America/New_York') AT TIME ZONE 'America/New_York';
(
  DATE_TRUNC('WEEK', (
    "ts_tz" AT TIME ZONE 'America/New_York'
  ) + INTERVAL '1 day') - INTERVAL '1 day'
) AT TIME ZONE 'America/New_York';
DATE_TRUNC('WEEK', "ts_tz" AT TIME ZONE 'America/New_York') AT TIME ZONE 'America/New_York';
DATE_TRUNC('DAY', "ts_tz" AT TIME ZONE 'America/New_York') AT TIME ZONE 'America/New_York';
DATE_TRUNC('HOUR', "ts_tz" AT TIME ZONE 'America/New_York') AT TIME ZONE 'America/New_York';
DATE_TRUNC('MINUTE', "ts_tz" AT TIME ZONE 'America/New_York') AT TIME ZONE 'America/New_York';
DATE_TRUNC('SECOND', "ts_tz" AT TIME ZONE 'America/New_York') AT TIME ZONE 'America/New_York';
DATE_TRUNC('MILLISECOND', "ts_tz" AT TIME ZONE 'America/New_York') AT TIME ZONE 'America/New_York';

-- === SNOWFLAKE ===
"ts_tz";
CONVERT_TIMEZONE(
  'America/New_York',
  'UTC',
  DATE_TRUNC('YEAR', CAST(CONVERT_TIMEZONE('America/New_York', "ts_tz") AS TIMESTAMPNTZ))
);
CONVERT_TIMEZONE(
  'America/New_York',
  'UTC',
  DATE_TRUNC('QUARTER', CAST(CONVERT_TIMEZONE('America/New_York', "ts_tz") AS TIMESTAMPNTZ))
);
CONVERT_TIMEZONE(
  'America/New_York',
  'UTC',
  DATE_TRUNC('MONTH', CAST(CONVERT_TIMEZONE('America/New_York', "ts_tz") AS TIMESTAMPNTZ))
);
CONVERT_TIMEZONE(
  'America/New_York',
  'UTC',
  DATEADD(
    DAY,
    -DAYOFWEEKISO(DATE_TRUNC('WEEK', CAST('2012-01-08' AS DATE))) % 7,
    DATE_TRUNC(
      'WEEK',
      DATEADD(
        DAY,
        DAYOFWEEKISO(DATE_TRUNC('WEEK', CAST('2012-01-08' AS DATE))) % 7,
        CAST(CONVERT_TIMEZONE('America/New_York', "ts_tz") AS TIMESTAMPNTZ)
      )
    )
  )
);
CONVERT_TIMEZONE(
  'America/New_York',
  'UTC',
  DATEADD(
    DAY,
    -(
      DAYOFWEEKISO(DATE_TRUNC('WEEK', CAST('2012-01-08' AS DATE))) - 1
    ) % 7,
    DATE_TRUNC(
      'WEEK',
      DATEADD(
        DAY,
        (
          DAYOFWEEKISO(DATE_TRUNC('WEEK', CAST('2012-01-08' AS DATE))) - 1
        ) % 7,
        CAST(CONVERT_TIMEZONE('America/New_York', "ts_tz") AS TIMESTAMPNTZ)
      )
    )
  )
);
CONVERT_TIMEZONE(
  'America/New_York',
  'UTC',
  DATE_TRUNC('DAY', CAST(CONVERT_TIMEZONE('America/New_York', "ts_tz") AS TIMESTAMPNTZ))
);
DATE_TRUNC('HOUR', "ts_tz");
DATE_TRUNC('MINUTE', "ts_tz");
DATE_TRUNC('SECOND', "ts_tz");
DATE_TRUNC('MILLISECOND', "ts_tz");

-- === SPARK ===
`ts_tz`;
TO_UTC_TIMESTAMP(
  CAST(DATE_TRUNC('YEAR', FROM_UTC_TIMESTAMP(CAST(`ts_tz` AS TIMESTAMP), 'America/New_York')) AS TIMESTAMP),
  'America/New_York'
);
TO_UTC_TIMESTAMP(
  CAST(DATE_TRUNC('QUARTER', FROM_UTC_TIMESTAMP(CAST(`ts_tz` AS TIMESTAMP), 'America/New_York')) AS TIMESTAMP),
  'America/New_York'
);
TO_UTC_TIMESTAMP(
  CAST(DATE_TRUNC('MONTH', FROM_UTC_TIMESTAMP(CAST(`ts_tz` AS TIMESTAMP), 'America/New_York')) AS TIMESTAMP),
  'America/New_York'
);
TO_UTC_TIMESTAMP(
  CAST(DATE_ADD(
    DATE_TRUNC(
      'WEEK',
      DATE_ADD(FROM_UTC_TIMESTAMP(CAST(`ts_tz` AS TIMESTAMP), 'America/New_York'), 1)
    ),
    -1
  ) AS TIMESTAMP),
  'America/New_York'
);
TO_UTC_TIMESTAMP(
  CAST(DATE_TRUNC('WEEK', FROM_UTC_TIMESTAMP(CAST(`ts_tz` AS TIMESTAMP), 'America/New_York')) AS TIMESTAMP),
  'America/New_York'
);
TO_UTC_TIMESTAMP(
  CAST(DATE_TRUNC('DAY', FROM_UTC_TIMESTAMP(CAST(`ts_tz` AS TIMESTAMP), 'America/New_York')) AS TIMESTAMP),
  'America/New_York'
);
TO_UTC_TIMESTAMP(
  CAST(DATE_TRUNC('HOUR', FROM_UTC_TIMESTAMP(CAST(`ts_tz` AS TIMESTAMP), 'America/New_York')) AS TIMESTAMP),
  'America/New_York'
);
TO_UTC_TIMESTAMP(
  CAST(DATE_TRUNC('MINUTE', FROM_UTC_TIMESTAMP(CAST(`ts_tz` AS TIMESTAMP), 'America/New_York')) AS TIMESTAMP),
  'America/New_York'
);
TO_UTC_TIMESTAMP(
  CAST(DATE_TRUNC('SECOND', FROM_UTC_TIMESTAMP(CAST(`ts_tz` AS TIMESTAMP), 'America/New_York')) AS TIMESTAMP),
  'America/New_York'
);
TO_UTC_TIMESTAMP(
  CAST(DATE_TRUNC('MILLISECOND', FROM_UTC_TIMESTAMP(CAST(`ts_tz` AS TIMESTAMP), 'America/New_York')) AS TIMESTAMP),
  'America/New_York'
);

-- === TRINO ===
"ts_tz";
DATE_TRUNC('YEAR', AT_TIMEZONE("ts_tz", 'America/New_York'));
DATE_TRUNC('QUARTER', AT_TIMEZONE("ts_tz", 'America/New_York'));
DATE_TRUNC('MONTH', AT_TIMEZONE("ts_tz", 'America/New_York'));
DATE_ADD(
  'DAY',
  -1,
  DATE_TRUNC('WEEK', DATE_ADD('DAY', 1, AT_TIMEZONE("ts_tz", 'America/New_York')))
);
DATE_TRUNC('WEEK', AT_TIMEZONE("ts_tz", 'America/New_York'));
DATE_TRUNC('DAY', AT_TIMEZONE("ts_tz", 'America/New_York'));
DATE_TRUNC('HOUR', AT_TIMEZONE("ts_tz", 'America/New_York'));
DATE_TRUNC('MINUTE', AT_TIMEZONE("ts_tz", 'America/New_York'));
DATE_TRUNC('SECOND', AT_TIMEZONE("ts_tz", 'America/New_York'));
DATE_TRUNC('MILLISECOND', AT_TIMEZONE("ts_tz", 'America/New_York'));
