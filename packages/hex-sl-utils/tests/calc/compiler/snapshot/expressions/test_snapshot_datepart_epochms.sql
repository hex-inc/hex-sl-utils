-- === CALCS ===
-- datetimetoepochms(d)
-- datetimetoepochms(ts)
-- datetimetoepochms(ts_tz)
-- epochmstodatetime(datetimetoepochms(d))
-- epochmstodatetime(datetimetoepochms(ts))
-- epochmstodatetime(datetimetoepochms(ts_tz))

-- === BIGQUERY ===
IF(NOT `d` IS NULL, UNIX_DATE(`d`) * 86400000, NULL);
IF(NOT `ts` IS NULL, UNIX_MILLIS(TIMESTAMP(`ts`)), NULL);
IF(NOT `ts_tz` IS NULL, UNIX_MILLIS(TIMESTAMP(DATETIME(`ts_tz`, 'UTC'))), NULL);
timestamp_millis(CAST(trunc(IF(NOT `d` IS NULL, UNIX_DATE(`d`) * 86400000, NULL)) AS INT64));
timestamp_millis(CAST(trunc(IF(NOT `ts` IS NULL, UNIX_MILLIS(TIMESTAMP(`ts`)), NULL)) AS INT64));
timestamp_millis(
  CAST(trunc(IF(NOT `ts_tz` IS NULL, UNIX_MILLIS(TIMESTAMP(DATETIME(`ts_tz`, 'UTC'))), NULL)) AS INT64)
);

-- === CLICKHOUSE ===
toRelativeSecondNum("d") * 1000;
(
  toUnixTimestamp64Milli("ts")
);
(
  toUnixTimestamp64Milli("ts_tz")
);
toDateTime64((
  toRelativeSecondNum("d") * 1000
) / 1000, 3, 'UTC');
toDateTime64((
  (
    toUnixTimestamp64Milli("ts")
  )
) / 1000, 3, 'UTC');
toDateTime64((
  (
    toUnixTimestamp64Milli("ts_tz")
  )
) / 1000, 3, 'UTC');

-- === DUCKDB ===
CAST(EPOCH_MS("d") AS BIGINT);
CAST(EPOCH_MS("ts") AS BIGINT);
CAST(EPOCH_MS("ts_tz" AT TIME ZONE 'UTC') AS BIGINT);
EPOCH_MS(CAST(CAST(EPOCH_MS("d") AS BIGINT) AS BIGINT)) AT TIME ZONE 'UTC';
EPOCH_MS(CAST(CAST(EPOCH_MS("ts") AS BIGINT) AS BIGINT)) AT TIME ZONE 'UTC';
EPOCH_MS(CAST(CAST(EPOCH_MS("ts_tz" AT TIME ZONE 'UTC') AS BIGINT) AS BIGINT)) AT TIME ZONE 'UTC';

-- === MSSQL ===
CAST(DATEDIFF(SECOND, CAST('1970-01-01 00:00:00' AS DATETIME2), CAST([d] AS DATETIME2)) AS BIGINT) * 1000;
(
  (
    CAST(DATEDIFF(SECOND, CAST('1970-01-01 00:00:00' AS DATETIME2), CAST([ts] AS DATETIME2)) AS BIGINT) * 1000
  ) + DATEPART(millisecond, [ts])
);
(
  (
    CAST(DATEDIFF(
      SECOND,
      CAST('1970-01-01 00:00:00' AS DATETIME2),
      CAST([ts_tz] AT TIME ZONE 'UTC' AS DATETIME2)
    ) AS BIGINT) * 1000
  ) + DATEPART(millisecond, [ts_tz] AT TIME ZONE 'UTC')
);
DATEADD(
  MICROSECOND,
  (
    (
      CAST(DATEDIFF(SECOND, CAST('1970-01-01 00:00:00' AS DATETIME2), CAST([d] AS DATETIME2)) AS BIGINT) * 1000
    ) % 1000
  ) * 1000,
  CAST(DATEADD(
    s,
    CAST(CAST(DATEDIFF(SECOND, CAST('1970-01-01 00:00:00' AS DATETIME2), CAST([d] AS DATETIME2)) AS BIGINT) * 1000 AS FLOAT) / 1000,
    '1970-01-01 00:00:00'
  ) AS DATETIME2)
) AT TIME ZONE 'UTC';
DATEADD(
  MICROSECOND,
  (
    (
      (
        (
          CAST(DATEDIFF(SECOND, CAST('1970-01-01 00:00:00' AS DATETIME2), CAST([ts] AS DATETIME2)) AS BIGINT) * 1000
        ) + DATEPART(millisecond, [ts])
      )
    ) % 1000
  ) * 1000,
  CAST(DATEADD(
    s,
    CAST((
      (
        CAST(DATEDIFF(SECOND, CAST('1970-01-01 00:00:00' AS DATETIME2), CAST([ts] AS DATETIME2)) AS BIGINT) * 1000
      ) + DATEPART(millisecond, [ts])
    ) AS FLOAT) / 1000,
    '1970-01-01 00:00:00'
  ) AS DATETIME2)
) AT TIME ZONE 'UTC';
DATEADD(
  MICROSECOND,
  (
    (
      (
        (
          CAST(DATEDIFF(
            SECOND,
            CAST('1970-01-01 00:00:00' AS DATETIME2),
            CAST([ts_tz] AT TIME ZONE 'UTC' AS DATETIME2)
          ) AS BIGINT) * 1000
        ) + DATEPART(millisecond, [ts_tz] AT TIME ZONE 'UTC')
      )
    ) % 1000
  ) * 1000,
  CAST(DATEADD(
    s,
    CAST((
      (
        CAST(DATEDIFF(
          SECOND,
          CAST('1970-01-01 00:00:00' AS DATETIME2),
          CAST([ts_tz] AT TIME ZONE 'UTC' AS DATETIME2)
        ) AS BIGINT) * 1000
      ) + DATEPART(millisecond, [ts_tz] AT TIME ZONE 'UTC')
    ) AS FLOAT) / 1000,
    '1970-01-01 00:00:00'
  ) AS DATETIME2)
) AT TIME ZONE 'UTC';

-- === MYSQL ===
FLOOR(UNIX_TIMESTAMP(`d`) * 1000);
FLOOR(UNIX_TIMESTAMP(`ts`) * 1000);
FLOOR(UNIX_TIMESTAMP(CAST(CONVERT_TZ(`ts_tz`, 'UTC', 'UTC') AS DATETIME(3))) * 1000);
FROM_UNIXTIME((
  FLOOR(UNIX_TIMESTAMP(`d`) * 1000)
) / 1000);
FROM_UNIXTIME((
  FLOOR(UNIX_TIMESTAMP(`ts`) * 1000)
) / 1000);
FROM_UNIXTIME(
  (
    FLOOR(UNIX_TIMESTAMP(CAST(CONVERT_TZ(`ts_tz`, 'UTC', 'UTC') AS DATETIME(3))) * 1000)
  ) / 1000
);

-- === POSTGRES ===
CAST(FLOOR(EXTRACT('epoch' FROM "d") * 1000) AS BIGINT);
CAST(FLOOR(EXTRACT('epoch' FROM "ts") * 1000) AS BIGINT);
CAST(FLOOR(EXTRACT('epoch' FROM "ts_tz" AT TIME ZONE 'UTC') * 1000) AS BIGINT);
TO_TIMESTAMP(
  CAST(CAST(FLOOR(EXTRACT('epoch' FROM "d") * 1000) AS BIGINT) AS DOUBLE PRECISION) / 1000
);
TO_TIMESTAMP(
  CAST(CAST(FLOOR(EXTRACT('epoch' FROM "ts") * 1000) AS BIGINT) AS DOUBLE PRECISION) / 1000
);
TO_TIMESTAMP(
  CAST(CAST(FLOOR(EXTRACT('epoch' FROM "ts_tz" AT TIME ZONE 'UTC') * 1000) AS BIGINT) AS DOUBLE PRECISION) / 1000
);

-- === REDSHIFT ===
CAST(EXTRACT('epoch' FROM "d") AS BIGINT) * 1000;
(
  (
    CAST(EXTRACT('millisecond' FROM "ts") AS BIGINT)
  ) + (
    CAST(EXTRACT('epoch' FROM "ts") AS BIGINT) * 1000
  )
);
(
  (
    CAST(EXTRACT('millisecond' FROM "ts_tz" AT TIME ZONE 'UTC') AS BIGINT)
  ) + (
    CAST(EXTRACT('epoch' FROM "ts_tz" AT TIME ZONE 'UTC') AS BIGINT) * 1000
  )
);
(
  CAST('epoch' AS TIMESTAMP) + (
    (
      CAST((
        CAST(EXTRACT('epoch' FROM "d") AS BIGINT) * 1000
      ) AS DOUBLE PRECISION) / 1000
    ) * INTERVAL '1 SECOND'
  )
);
(
  CAST('epoch' AS TIMESTAMP) + (
    (
      CAST((
        (
          (
            CAST(EXTRACT('millisecond' FROM "ts") AS BIGINT)
          ) + (
            CAST(EXTRACT('epoch' FROM "ts") AS BIGINT) * 1000
          )
        )
      ) AS DOUBLE PRECISION) / 1000
    ) * INTERVAL '1 SECOND'
  )
);
(
  CAST('epoch' AS TIMESTAMP) + (
    (
      CAST((
        (
          (
            CAST(EXTRACT('millisecond' FROM "ts_tz" AT TIME ZONE 'UTC') AS BIGINT)
          ) + (
            CAST(EXTRACT('epoch' FROM "ts_tz" AT TIME ZONE 'UTC') AS BIGINT) * 1000
          )
        )
      ) AS DOUBLE PRECISION) / 1000
    ) * INTERVAL '1 SECOND'
  )
);

-- === SNOWFLAKE ===
DATE_PART('epoch_second', "d") * 1000;
DATE_PART('epoch_millisecond', "ts");
DATE_PART('epoch_millisecond', CONVERT_TIMEZONE('UTC', "ts_tz"));
TO_TIMESTAMP_TZ(DATE_PART('epoch_second', "d") * 1000, 3);
TO_TIMESTAMP_TZ(DATE_PART('epoch_millisecond', "ts"), 3);
TO_TIMESTAMP_TZ(DATE_PART('epoch_millisecond', CONVERT_TIMEZONE('UTC', "ts_tz")), 3);

-- === SPARK ===
(
  UNIX_TIMESTAMP(FROM_UTC_TIMESTAMP(CAST(`d` AS TIMESTAMP), CURRENT_TIMEZONE())) * 1000 + CAST(EXTRACT(seconds FROM `d`) % 1 * 1000 AS BIGINT)
);
(
  UNIX_TIMESTAMP(FROM_UTC_TIMESTAMP(CAST(`ts` AS TIMESTAMP), CURRENT_TIMEZONE())) * 1000 + CAST(EXTRACT(seconds FROM `ts`) % 1 * 1000 AS BIGINT)
);
(
  UNIX_TIMESTAMP(`ts_tz`) * 1000 + CAST(EXTRACT(seconds FROM `ts_tz`) % 1 * 1000 AS BIGINT)
);
DATE_ADD(
  MILLISECOND,
  (
    (
      UNIX_TIMESTAMP(FROM_UTC_TIMESTAMP(CAST(`d` AS TIMESTAMP), CURRENT_TIMEZONE())) * 1000 + CAST(EXTRACT(seconds FROM `d`) % 1 * 1000 AS BIGINT)
    )
  ) % 1000,
  TO_UTC_TIMESTAMP(
    CAST(FROM_UNIXTIME(
      (
        (
          UNIX_TIMESTAMP(FROM_UTC_TIMESTAMP(CAST(`d` AS TIMESTAMP), CURRENT_TIMEZONE())) * 1000 + CAST(EXTRACT(seconds FROM `d`) % 1 * 1000 AS BIGINT)
        )
      ) / 1000
    ) AS TIMESTAMP),
    CURRENT_TIMEZONE()
  )
);
DATE_ADD(
  MILLISECOND,
  (
    (
      UNIX_TIMESTAMP(FROM_UTC_TIMESTAMP(CAST(`ts` AS TIMESTAMP), CURRENT_TIMEZONE())) * 1000 + CAST(EXTRACT(seconds FROM `ts`) % 1 * 1000 AS BIGINT)
    )
  ) % 1000,
  TO_UTC_TIMESTAMP(
    CAST(FROM_UNIXTIME(
      (
        (
          UNIX_TIMESTAMP(FROM_UTC_TIMESTAMP(CAST(`ts` AS TIMESTAMP), CURRENT_TIMEZONE())) * 1000 + CAST(EXTRACT(seconds FROM `ts`) % 1 * 1000 AS BIGINT)
        )
      ) / 1000
    ) AS TIMESTAMP),
    CURRENT_TIMEZONE()
  )
);
DATE_ADD(
  MILLISECOND,
  (
    (
      UNIX_TIMESTAMP(`ts_tz`) * 1000 + CAST(EXTRACT(seconds FROM `ts_tz`) % 1 * 1000 AS BIGINT)
    )
  ) % 1000,
  TO_UTC_TIMESTAMP(
    CAST(FROM_UNIXTIME(
      (
        (
          UNIX_TIMESTAMP(`ts_tz`) * 1000 + CAST(EXTRACT(seconds FROM `ts_tz`) % 1 * 1000 AS BIGINT)
        )
      ) / 1000
    ) AS TIMESTAMP),
    CURRENT_TIMEZONE()
  )
);

-- === TRINO ===
CAST(FLOOR(TO_UNIXTIME("d") * 1000) AS BIGINT);
CAST(FLOOR(TO_UNIXTIME("ts") * 1000) AS BIGINT);
CAST(FLOOR(TO_UNIXTIME(AT_TIMEZONE("ts_tz", 'UTC')) * 1000) AS BIGINT);
WITH_TIMEZONE(
  DATE_ADD(
    'MILLISECOND',
    (
      (
        CAST(FLOOR(TO_UNIXTIME("d") * 1000) AS BIGINT)
      ) % 1000
    ),
    CAST(FROM_UNIXTIME(
      FLOOR(
        CAST(CAST(CAST(FLOOR(TO_UNIXTIME("d") * 1000) AS BIGINT) AS BIGINT) AS DOUBLE) / 1000
      )
    ) AS TIMESTAMP)
  ),
  'UTC'
);
WITH_TIMEZONE(
  DATE_ADD(
    'MILLISECOND',
    (
      (
        CAST(FLOOR(TO_UNIXTIME("ts") * 1000) AS BIGINT)
      ) % 1000
    ),
    CAST(FROM_UNIXTIME(
      FLOOR(
        CAST(CAST(CAST(FLOOR(TO_UNIXTIME("ts") * 1000) AS BIGINT) AS BIGINT) AS DOUBLE) / 1000
      )
    ) AS TIMESTAMP)
  ),
  'UTC'
);
WITH_TIMEZONE(
  DATE_ADD(
    'MILLISECOND',
    (
      (
        CAST(FLOOR(TO_UNIXTIME(AT_TIMEZONE("ts_tz", 'UTC')) * 1000) AS BIGINT)
      ) % 1000
    ),
    CAST(FROM_UNIXTIME(
      FLOOR(
        CAST(CAST(CAST(FLOOR(TO_UNIXTIME(AT_TIMEZONE("ts_tz", 'UTC')) * 1000) AS BIGINT) AS BIGINT) AS DOUBLE) / 1000
      )
    ) AS TIMESTAMP)
  ),
  'UTC'
);
