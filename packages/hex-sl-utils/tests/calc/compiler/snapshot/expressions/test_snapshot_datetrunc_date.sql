-- === CALCS ===
-- d
-- truncyear(d)
-- truncquarter(d)
-- truncmonth(d)
-- truncweek(d)
-- truncweekmonday(d)
-- truncday(d)
-- trunchour(d)
-- truncminute(d)
-- truncsecond(d)
-- truncmillisecond(d)

-- === BIGQUERY ===
`d`;
CAST(DATE_TRUNC(`d`, YEAR) AS DATE);
CAST(DATE_TRUNC(`d`, QUARTER) AS DATE);
CAST(DATE_TRUNC(`d`, MONTH) AS DATE);
CAST(DATE_TRUNC(`d`, WEEK) AS DATE);
CAST(DATE_TRUNC(`d`, WEEK(MONDAY)) AS DATE);
CAST(DATE_TRUNC(`d`, DAY) AS DATE);
`d`;
`d`;
`d`;
`d`;

-- === CLICKHOUSE ===
"d";
toDate(dateTrunc('year', "d"));
toDate(dateTrunc('quarter', "d"));
toDate(dateTrunc('month', "d"));
toDate(dateTrunc('week', "d" + INTERVAL 1 day) - INTERVAL 1 day);
toDate(dateTrunc('week', "d"));
toDate(dateTrunc('day', "d"));
"d";
"d";
"d";
"d";

-- === DUCKDB ===
"d";
CAST(DATE_TRUNC('YEAR', "d") AS DATE);
CAST(DATE_TRUNC('QUARTER', "d") AS DATE);
CAST(DATE_TRUNC('MONTH', "d") AS DATE);
CAST(DATE_TRUNC('WEEK', (
  "d" + INTERVAL 1 day
)) - INTERVAL 1 day AS DATE);
CAST(DATE_TRUNC('WEEK', "d") AS DATE);
CAST(DATE_TRUNC('DAY', "d") AS DATE);
"d";
"d";
"d";
"d";

-- === MSSQL ===
[d];
CAST(DATETIME2FROMPARTS(DATEPART(year, [d]), 1, 1, 0, 0, 0, 0, 3) AS DATE);
CAST(DATETIME2FROMPARTS(
  DATEPART(year, [d]),
  FLOOR(CAST((
    DATEPART(month, [d]) - 1
  ) AS FLOAT) / 3) * 3 + 1,
  1,
  0,
  0,
  0,
  0,
  3
) AS DATE);
CAST(DATETIME2FROMPARTS(DATEPART(year, [d]), DATEPART(month, [d]), 1, 0, 0, 0, 0, 3) AS DATE);
CAST(DATEADD(
  DAY,
  -DATEPART(weekday, [d]) + 1,
  DATETIME2FROMPARTS(DATEPART(year, [d]), DATEPART(month, [d]), DATEPART(day, [d]), 0, 0, 0, 0, 3)
) AS DATE);
CAST(DATEADD(
  DAY,
  -(
    (
      (
        DATEPART(weekday, [d]) + 5
      ) % 7
    ) + 1
  ) + 1,
  DATETIME2FROMPARTS(DATEPART(year, [d]), DATEPART(month, [d]), DATEPART(day, [d]), 0, 0, 0, 0, 3)
) AS DATE);
CAST(DATETIME2FROMPARTS(DATEPART(year, [d]), DATEPART(month, [d]), DATEPART(day, [d]), 0, 0, 0, 0, 3) AS DATE);
[d];
[d];
[d];
[d];

-- === MYSQL ===
`d`;
CAST(CAST(DATE_FORMAT(`d`, '%Y-01-01') AS DATE) AS DATE);
CAST(CAST(DATE_FORMAT(`d`, CONCAT('%Y-', (
  (
    QUARTER(`d`) - 1
  ) * 3 + 1
), '-01')) AS DATE) AS DATE);
CAST(CAST(DATE_FORMAT(`d`, '%Y-%m-01') AS DATE) AS DATE);
CAST(DATE_SUB(
  CAST(DATE_FORMAT(`d`, '%Y-%m-%d') AS DATE),
  INTERVAL (DAYOFWEEK(DATE(`d`)) - 1) DAY
) AS DATE);
CAST(DATE_SUB(CAST(DATE_FORMAT(`d`, '%Y-%m-%d') AS DATE), INTERVAL (WEEKDAY(DATE(`d`))) DAY) AS DATE);
CAST(CAST(DATE_FORMAT(`d`, '%Y-%m-%d') AS DATE) AS DATE);
`d`;
`d`;
`d`;
`d`;

-- === POSTGRES ===
"d";
CAST(DATE_TRUNC('YEAR', "d") AS DATE);
CAST(DATE_TRUNC('QUARTER', "d") AS DATE);
CAST(DATE_TRUNC('MONTH', "d") AS DATE);
CAST(DATE_TRUNC('WEEK', (
  "d" + INTERVAL '1 day'
)) - INTERVAL '1 day' AS DATE);
CAST(DATE_TRUNC('WEEK', "d") AS DATE);
CAST(DATE_TRUNC('DAY', "d") AS DATE);
"d";
"d";
"d";
"d";

-- === REDSHIFT ===
"d";
CAST(DATE_TRUNC('YEAR', "d") AS DATE);
CAST(DATE_TRUNC('QUARTER', "d") AS DATE);
CAST(DATE_TRUNC('MONTH', "d") AS DATE);
CAST((
  DATE_TRUNC('WEEK', (
    "d"
  ) + INTERVAL '1 day') - INTERVAL '1 day'
) AS DATE);
CAST(DATE_TRUNC('WEEK', "d") AS DATE);
CAST(DATE_TRUNC('DAY', "d") AS DATE);
"d";
"d";
"d";
"d";

-- === SNOWFLAKE ===
"d";
DATE_TRUNC('YEAR', "d");
DATE_TRUNC('QUARTER', "d");
DATE_TRUNC('MONTH', "d");
DATEADD(
  DAY,
  -DAYOFWEEKISO(DATE_TRUNC('WEEK', CAST('2012-01-08' AS DATE))) % 7,
  DATE_TRUNC(
    'WEEK',
    DATEADD(DAY, DAYOFWEEKISO(DATE_TRUNC('WEEK', CAST('2012-01-08' AS DATE))) % 7, "d")
  )
);
DATEADD(
  DAY,
  -(
    DAYOFWEEKISO(DATE_TRUNC('WEEK', CAST('2012-01-08' AS DATE))) - 1
  ) % 7,
  DATE_TRUNC(
    'WEEK',
    DATEADD(DAY, (
      DAYOFWEEKISO(DATE_TRUNC('WEEK', CAST('2012-01-08' AS DATE))) - 1
    ) % 7, "d")
  )
);
DATE_TRUNC('DAY', "d");
"d";
"d";
"d";
"d";

-- === SPARK ===
`d`;
CAST(DATE_TRUNC('YEAR', `d`) AS DATE);
CAST(DATE_TRUNC('QUARTER', `d`) AS DATE);
CAST(DATE_TRUNC('MONTH', `d`) AS DATE);
CAST(DATE_ADD(DATE_TRUNC('WEEK', DATE_ADD(`d`, 1)), -1) AS DATE);
CAST(DATE_TRUNC('WEEK', `d`) AS DATE);
CAST(DATE_TRUNC('DAY', `d`) AS DATE);
`d`;
`d`;
`d`;
`d`;

-- === TRINO ===
"d";
CAST(DATE_TRUNC('YEAR', "d") AS DATE);
CAST(DATE_TRUNC('QUARTER', "d") AS DATE);
CAST(DATE_TRUNC('MONTH', "d") AS DATE);
CAST(DATE_ADD('DAY', -1, DATE_TRUNC('WEEK', DATE_ADD('DAY', 1, "d"))) AS DATE);
CAST(DATE_TRUNC('WEEK', "d") AS DATE);
CAST(DATE_TRUNC('DAY', "d") AS DATE);
"d";
"d";
"d";
"d";
