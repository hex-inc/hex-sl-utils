-- === CALCS ===
-- ts
-- truncyear(ts)
-- truncquarter(ts)
-- truncmonth(ts)
-- truncweek(ts)
-- truncweekmonday(ts)
-- truncday(ts)
-- trunchour(ts)
-- truncminute(ts)
-- truncsecond(ts)
-- truncmillisecond(ts)

-- === BIGQUERY ===
`ts`;
DATE_TRUNC(`ts`, YEAR);
DATE_TRUNC(`ts`, QUARTER);
DATE_TRUNC(`ts`, MONTH);
DATE_TRUNC(`ts`, WEEK);
DATE_TRUNC(`ts`, WEEK(MONDAY));
DATE_TRUNC(`ts`, DAY);
DATE_TRUNC(`ts`, HOUR);
DATE_TRUNC(`ts`, MINUTE);
DATE_TRUNC(`ts`, SECOND);
DATE_TRUNC(`ts`, MILLISECOND);

-- === CLICKHOUSE ===
"ts";
toDateTime64(dateTrunc('year', "ts"), 3);
toDateTime64(dateTrunc('quarter', "ts"), 3);
toDateTime64(dateTrunc('month', "ts"), 3);
toDateTime64(dateTrunc('week', "ts" + INTERVAL 1 day) - INTERVAL 1 day, 3);
toDateTime64(dateTrunc('week', "ts"), 3);
toDateTime64(dateTrunc('day', "ts"), 3);
dateTrunc('hour', "ts");
dateTrunc('minute', "ts");
dateTrunc('second', "ts");
dateTrunc('millisecond', "ts");

-- === DUCKDB ===
"ts";
CAST(DATE_TRUNC('YEAR', "ts") AS TIMESTAMP);
CAST(DATE_TRUNC('QUARTER', "ts") AS TIMESTAMP);
CAST(DATE_TRUNC('MONTH', "ts") AS TIMESTAMP);
CAST(DATE_TRUNC('WEEK', (
  "ts" + INTERVAL 1 day
)) - INTERVAL 1 day AS TIMESTAMP);
CAST(DATE_TRUNC('WEEK', "ts") AS TIMESTAMP);
CAST(DATE_TRUNC('DAY', "ts") AS TIMESTAMP);
DATE_TRUNC('HOUR', "ts");
DATE_TRUNC('MINUTE', "ts");
DATE_TRUNC('SECOND', "ts");
DATE_TRUNC('MILLISECOND', "ts");

-- === MSSQL ===
[ts];
DATETIME2FROMPARTS(DATEPART(year, [ts]), 1, 1, 0, 0, 0, 0, 3);
DATETIME2FROMPARTS(
  DATEPART(year, [ts]),
  FLOOR(CAST((
    DATEPART(month, [ts]) - 1
  ) AS FLOAT) / 3) * 3 + 1,
  1,
  0,
  0,
  0,
  0,
  3
);
DATETIME2FROMPARTS(DATEPART(year, [ts]), DATEPART(month, [ts]), 1, 0, 0, 0, 0, 3);
DATEADD(
  DAY,
  -DATEPART(weekday, [ts]) + 1,
  DATETIME2FROMPARTS(DATEPART(year, [ts]), DATEPART(month, [ts]), DATEPART(day, [ts]), 0, 0, 0, 0, 3)
);
DATEADD(
  DAY,
  -(
    (
      (
        DATEPART(weekday, [ts]) + 5
      ) % 7
    ) + 1
  ) + 1,
  DATETIME2FROMPARTS(DATEPART(year, [ts]), DATEPART(month, [ts]), DATEPART(day, [ts]), 0, 0, 0, 0, 3)
);
DATETIME2FROMPARTS(DATEPART(year, [ts]), DATEPART(month, [ts]), DATEPART(day, [ts]), 0, 0, 0, 0, 3);
DATETIME2FROMPARTS(
  DATEPART(year, [ts]),
  DATEPART(month, [ts]),
  DATEPART(day, [ts]),
  DATEPART(hour, [ts]),
  0,
  0,
  0,
  3
);
DATETIME2FROMPARTS(
  DATEPART(year, [ts]),
  DATEPART(month, [ts]),
  DATEPART(day, [ts]),
  DATEPART(hour, [ts]),
  DATEPART(minute, [ts]),
  0,
  0,
  3
);
DATETIME2FROMPARTS(
  DATEPART(year, [ts]),
  DATEPART(month, [ts]),
  DATEPART(day, [ts]),
  DATEPART(hour, [ts]),
  DATEPART(minute, [ts]),
  DATEPART(second, [ts]),
  0,
  3
);
DATETIME2FROMPARTS(
  DATEPART(year, [ts]),
  DATEPART(month, [ts]),
  DATEPART(day, [ts]),
  DATEPART(hour, [ts]),
  DATEPART(minute, [ts]),
  DATEPART(second, [ts]),
  DATEPART(millisecond, [ts]),
  3
);

-- === MYSQL ===
`ts`;
TIMESTAMP(CAST(DATE_FORMAT(`ts`, '%Y-01-01') AS DATE));
TIMESTAMP(
  CAST(DATE_FORMAT(`ts`, CONCAT('%Y-', (
    (
      QUARTER(`ts`) - 1
    ) * 3 + 1
  ), '-01')) AS DATE)
);
TIMESTAMP(CAST(DATE_FORMAT(`ts`, '%Y-%m-01') AS DATE));
TIMESTAMP(
  DATE_SUB(
    CAST(DATE_FORMAT(`ts`, '%Y-%m-%d') AS DATE),
    INTERVAL (DAYOFWEEK(DATE(`ts`)) - 1) DAY
  )
);
TIMESTAMP(
  DATE_SUB(CAST(DATE_FORMAT(`ts`, '%Y-%m-%d') AS DATE), INTERVAL (WEEKDAY(DATE(`ts`))) DAY)
);
TIMESTAMP(CAST(DATE_FORMAT(`ts`, '%Y-%m-%d') AS DATE));
TIMESTAMP(CAST(DATE_FORMAT(`ts`, '%Y-%m-%d %H:00:00') AS DATETIME));
TIMESTAMP(CAST(DATE_FORMAT(`ts`, '%Y-%m-%d %H:%i:00') AS DATETIME));
TIMESTAMP(CAST(DATE_FORMAT(`ts`, '%Y-%m-%d %T') AS DATETIME));
TIMESTAMP(CAST(DATE_FORMAT(`ts`, '%Y-%m-%d %T.%f') AS DATETIME(3)));

-- === POSTGRES ===
"ts";
CAST(DATE_TRUNC('YEAR', "ts") AS TIMESTAMP);
CAST(DATE_TRUNC('QUARTER', "ts") AS TIMESTAMP);
CAST(DATE_TRUNC('MONTH', "ts") AS TIMESTAMP);
CAST(DATE_TRUNC('WEEK', (
  "ts" + INTERVAL '1 day'
)) - INTERVAL '1 day' AS TIMESTAMP);
CAST(DATE_TRUNC('WEEK', "ts") AS TIMESTAMP);
CAST(DATE_TRUNC('DAY', "ts") AS TIMESTAMP);
DATE_TRUNC('HOUR', "ts");
DATE_TRUNC('MINUTE', "ts");
DATE_TRUNC('SECOND', "ts");
DATE_TRUNC('MILLISECOND', "ts");

-- === REDSHIFT ===
"ts";
DATE_TRUNC('YEAR', "ts");
DATE_TRUNC('QUARTER', "ts");
DATE_TRUNC('MONTH', "ts");
(
  DATE_TRUNC('WEEK', (
    "ts"
  ) + INTERVAL '1 day') - INTERVAL '1 day'
);
DATE_TRUNC('WEEK', "ts");
DATE_TRUNC('DAY', "ts");
DATE_TRUNC('HOUR', "ts");
DATE_TRUNC('MINUTE', "ts");
DATE_TRUNC('SECOND', "ts");
DATE_TRUNC('MILLISECOND', "ts");

-- === SNOWFLAKE ===
"ts";
DATE_TRUNC('YEAR', "ts");
DATE_TRUNC('QUARTER', "ts");
DATE_TRUNC('MONTH', "ts");
DATEADD(
  DAY,
  -DAYOFWEEKISO(DATE_TRUNC('WEEK', CAST('2012-01-08' AS DATE))) % 7,
  DATE_TRUNC(
    'WEEK',
    DATEADD(DAY, DAYOFWEEKISO(DATE_TRUNC('WEEK', CAST('2012-01-08' AS DATE))) % 7, "ts")
  )
);
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
      "ts"
    )
  )
);
DATE_TRUNC('DAY', "ts");
DATE_TRUNC('HOUR', "ts");
DATE_TRUNC('MINUTE', "ts");
DATE_TRUNC('SECOND', "ts");
DATE_TRUNC('MILLISECOND', "ts");

-- === SPARK ===
`ts`;
CAST(DATE_TRUNC('YEAR', `ts`) AS TIMESTAMP);
CAST(DATE_TRUNC('QUARTER', `ts`) AS TIMESTAMP);
CAST(DATE_TRUNC('MONTH', `ts`) AS TIMESTAMP);
CAST(DATE_ADD(DATE_TRUNC('WEEK', DATE_ADD(`ts`, 1)), -1) AS TIMESTAMP);
CAST(DATE_TRUNC('WEEK', `ts`) AS TIMESTAMP);
CAST(DATE_TRUNC('DAY', `ts`) AS TIMESTAMP);
DATE_TRUNC('HOUR', `ts`);
DATE_TRUNC('MINUTE', `ts`);
DATE_TRUNC('SECOND', `ts`);
DATE_TRUNC('MILLISECOND', `ts`);

-- === TRINO ===
"ts";
DATE_TRUNC('YEAR', "ts");
DATE_TRUNC('QUARTER', "ts");
DATE_TRUNC('MONTH', "ts");
DATE_ADD('DAY', -1, DATE_TRUNC('WEEK', DATE_ADD('DAY', 1, "ts")));
DATE_TRUNC('WEEK', "ts");
DATE_TRUNC('DAY', "ts");
DATE_TRUNC('HOUR', "ts");
DATE_TRUNC('MINUTE', "ts");
DATE_TRUNC('SECOND', "ts");
DATE_TRUNC('MILLISECOND', "ts");
