-- === CALCS ===
-- _chart_toNumber(str_int)
-- _chart_toNumber(str_float)
-- _chart_toNumber(bool_col)
-- _chart_toNumber(date_col)
-- _chart_toNumber(timestamp_col)
-- _chart_toNumber(int_col)
-- _chart_toNumber(float_col)
-- _chart_toDatetime(str_date)
-- _chart_toDatetime(str_datetime)
-- _chart_toDatetime(epoch_ms)
-- _chart_toDatetime(bool_col)
-- _chart_toDatetime(date_col)
-- _chart_toDatetime(timestamp_col)
-- _chart_toNumber(_chart_toDatetime(str_date))
-- _chart_toDatetime(_chart_toNumber(bool_col))

-- === BIGQUERY ===
SAFE_CAST(`str_int` AS FLOAT64);
SAFE_CAST(`str_float` AS FLOAT64);
CASE WHEN `bool_col` THEN 1 ELSE 0 END;
IF(NOT `date_col` IS NULL, UNIX_DATE(`date_col`) * 86400000, NULL);
IF(NOT `timestamp_col` IS NULL, UNIX_MILLIS(TIMESTAMP(`timestamp_col`)), NULL);
`int_col`;
`float_col`;
SAFE_CAST(`str_date` AS DATETIME);
SAFE_CAST(`str_datetime` AS DATETIME);
timestamp_millis(CAST(trunc(`epoch_ms`) AS INT64));
timestamp_millis(CAST(trunc(CASE WHEN `bool_col` THEN 1 ELSE 0 END) AS INT64));
CAST(`date_col` AS DATETIME);
`timestamp_col`;
IF(
  NOT SAFE_CAST(`str_date` AS DATETIME) IS NULL,
  UNIX_MILLIS(TIMESTAMP(SAFE_CAST(`str_date` AS DATETIME))),
  NULL
);
timestamp_millis(CAST(trunc(CASE WHEN `bool_col` THEN 1 ELSE 0 END) AS INT64));

-- === CLICKHOUSE ===
accurateCastOrNull("str_int", 'Nullable(Float64)');
accurateCastOrNull("str_float", 'Nullable(Float64)');
CASE WHEN "bool_col" THEN 1 ELSE 0 END;
toRelativeSecondNum("date_col") * 1000;
(
  toUnixTimestamp64Milli("timestamp_col")
);
"int_col";
"float_col";
parseDateTime64BestEffortOrNull("str_date", 3, 'UTC');
parseDateTime64BestEffortOrNull("str_datetime", 3, 'UTC');
toDateTime64((
  "epoch_ms"
) / 1000, 3, 'UTC');
toDateTime64((
  CASE WHEN "bool_col" THEN 1 ELSE 0 END
) / 1000, 3, 'UTC');
toDateTime64("date_col", 3);
"timestamp_col";
(
  toUnixTimestamp64Milli(parseDateTime64BestEffortOrNull("str_date", 3, 'UTC'))
);
toDateTime64((
  CASE WHEN "bool_col" THEN 1 ELSE 0 END
) / 1000, 3, 'UTC');

-- === DUCKDB ===
TRY_CAST("str_int" AS DOUBLE);
TRY_CAST("str_float" AS DOUBLE);
CASE WHEN "bool_col" THEN 1 ELSE 0 END;
CAST(EPOCH_MS("date_col") AS BIGINT);
CAST(EPOCH_MS("timestamp_col") AS BIGINT);
"int_col";
"float_col";
TRY_CAST(TRY_STRPTIME(
  "str_date",
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
  "str_datetime",
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
EPOCH_MS(CAST("epoch_ms" AS BIGINT)) AT TIME ZONE 'UTC';
EPOCH_MS(CAST(CASE WHEN "bool_col" THEN 1 ELSE 0 END AS BIGINT)) AT TIME ZONE 'UTC';
CAST("date_col" AS TIMESTAMP);
"timestamp_col";
CAST(EPOCH_MS(
  TRY_CAST(TRY_STRPTIME(
    "str_date",
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
  ) AS TIMESTAMP)
) AS BIGINT);
EPOCH_MS(CAST(CASE WHEN "bool_col" THEN 1 ELSE 0 END AS BIGINT)) AT TIME ZONE 'UTC';

-- === MSSQL ===
TRY_CAST([str_int] AS FLOAT);
TRY_CAST([str_float] AS FLOAT);
CASE WHEN [bool_col] <> 0 THEN 1 ELSE 0 END;
CAST(DATEDIFF(SECOND, CAST('1970-01-01 00:00:00' AS DATETIME2), CAST([date_col] AS DATETIME2)) AS BIGINT) * 1000;
(
  (
    CAST(DATEDIFF(SECOND, CAST('1970-01-01 00:00:00' AS DATETIME2), CAST([timestamp_col] AS DATETIME2)) AS BIGINT) * 1000
  ) + DATEPART(millisecond, [timestamp_col])
);
[int_col];
[float_col];
TRY_CAST([str_date] AS DATETIME2);
TRY_CAST([str_datetime] AS DATETIME2);
DATEADD(
  MICROSECOND,
  (
    (
      [epoch_ms]
    ) % 1000
  ) * 1000,
  CAST(DATEADD(s, CAST([epoch_ms] AS FLOAT) / 1000, '1970-01-01 00:00:00') AS DATETIME2)
) AT TIME ZONE 'UTC';
DATEADD(
  MICROSECOND,
  (
    (
      CASE WHEN [bool_col] <> 0 THEN 1 ELSE 0 END
    ) % 1000
  ) * 1000,
  CAST(DATEADD(
    s,
    CAST(CASE WHEN [bool_col] <> 0 THEN 1 ELSE 0 END AS FLOAT) / 1000,
    '1970-01-01 00:00:00'
  ) AS DATETIME2)
) AT TIME ZONE 'UTC';
CAST([date_col] AS DATETIME2);
[timestamp_col];
(
  (
    CAST(DATEDIFF(
      SECOND,
      CAST('1970-01-01 00:00:00' AS DATETIME2),
      CAST(TRY_CAST([str_date] AS DATETIME2) AS DATETIME2)
    ) AS BIGINT) * 1000
  ) + DATEPART(millisecond, TRY_CAST([str_date] AS DATETIME2))
);
DATEADD(
  MICROSECOND,
  (
    (
      CASE WHEN [bool_col] <> 0 THEN 1 ELSE 0 END
    ) % 1000
  ) * 1000,
  CAST(DATEADD(
    s,
    CAST(CASE WHEN [bool_col] <> 0 THEN 1 ELSE 0 END AS FLOAT) / 1000,
    '1970-01-01 00:00:00'
  ) AS DATETIME2)
) AT TIME ZONE 'UTC';

-- === MYSQL ===
CASE
  WHEN (`str_int` RLIKE '^[-+]?[0-9]*\\.?[0-9]+$')
  THEN CAST(`str_int` AS DOUBLE)
  ELSE NULL
END;
CASE
  WHEN (`str_float` RLIKE '^[-+]?[0-9]*\\.?[0-9]+$')
  THEN CAST(`str_float` AS DOUBLE)
  ELSE NULL
END;
CASE WHEN `bool_col` THEN 1 ELSE 0 END;
FLOOR(UNIX_TIMESTAMP(`date_col`) * 1000);
FLOOR(UNIX_TIMESTAMP(`timestamp_col`) * 1000);
`int_col`;
`float_col`;
CAST(`str_date` AS DATETIME(3));
CAST(`str_datetime` AS DATETIME(3));
FROM_UNIXTIME((
  `epoch_ms`
) / 1000);
FROM_UNIXTIME((
  CASE WHEN `bool_col` THEN 1 ELSE 0 END
) / 1000);
CAST(`date_col` AS DATETIME);
`timestamp_col`;
FLOOR(UNIX_TIMESTAMP(CAST(`str_date` AS DATETIME(3))) * 1000);
FROM_UNIXTIME((
  CASE WHEN `bool_col` THEN 1 ELSE 0 END
) / 1000);

-- === POSTGRES ===
CASE
  WHEN "str_int" ~ '^[-+]?[0-9]*\.?[0-9]+$'
  THEN CAST("str_int" AS DOUBLE PRECISION)
  ELSE NULL
END;
CASE
  WHEN "str_float" ~ '^[-+]?[0-9]*\.?[0-9]+$'
  THEN CAST("str_float" AS DOUBLE PRECISION)
  ELSE NULL
END;
CASE WHEN "bool_col" THEN 1 ELSE 0 END;
CAST(FLOOR(EXTRACT('epoch' FROM "date_col") * 1000) AS BIGINT);
CAST(FLOOR(EXTRACT('epoch' FROM "timestamp_col") * 1000) AS BIGINT);
"int_col";
"float_col";
CAST("str_date" AS TIMESTAMP);
CAST("str_datetime" AS TIMESTAMP);
TO_TIMESTAMP(CAST("epoch_ms" AS DOUBLE PRECISION) / 1000);
TO_TIMESTAMP(CAST(CASE WHEN "bool_col" THEN 1 ELSE 0 END AS DOUBLE PRECISION) / 1000);
CAST("date_col" AS TIMESTAMP);
"timestamp_col";
CAST(FLOOR(EXTRACT('epoch' FROM CAST("str_date" AS TIMESTAMP)) * 1000) AS BIGINT);
TO_TIMESTAMP(CAST(CASE WHEN "bool_col" THEN 1 ELSE 0 END AS DOUBLE PRECISION) / 1000);

-- === REDSHIFT ===
CASE
  WHEN "str_int" ~ '^[-+]?[0-9]*\\.?[0-9]+$'
  THEN CAST("str_int" AS DOUBLE PRECISION)
  ELSE NULL
END;
CASE
  WHEN "str_float" ~ '^[-+]?[0-9]*\\.?[0-9]+$'
  THEN CAST("str_float" AS DOUBLE PRECISION)
  ELSE NULL
END;
CASE WHEN "bool_col" THEN 1 ELSE 0 END;
CAST(EXTRACT('epoch' FROM "date_col") AS BIGINT) * 1000;
(
  (
    CAST(EXTRACT('millisecond' FROM "timestamp_col") AS BIGINT)
  ) + (
    CAST(EXTRACT('epoch' FROM "timestamp_col") AS BIGINT) * 1000
  )
);
"int_col";
"float_col";
CAST("str_date" AS TIMESTAMP);
CAST("str_datetime" AS TIMESTAMP);
(
  CAST('epoch' AS TIMESTAMP) + (
    (
      CAST((
        "epoch_ms"
      ) AS DOUBLE PRECISION) / 1000
    ) * INTERVAL '1 SECOND'
  )
);
(
  CAST('epoch' AS TIMESTAMP) + (
    (
      CAST((
        CASE WHEN "bool_col" THEN 1 ELSE 0 END
      ) AS DOUBLE PRECISION) / 1000
    ) * INTERVAL '1 SECOND'
  )
);
CAST("date_col" AS TIMESTAMP);
"timestamp_col";
(
  (
    CAST(EXTRACT('millisecond' FROM CAST("str_date" AS TIMESTAMP)) AS BIGINT)
  ) + (
    CAST(EXTRACT('epoch' FROM CAST("str_date" AS TIMESTAMP)) AS BIGINT) * 1000
  )
);
(
  CAST('epoch' AS TIMESTAMP) + (
    (
      CAST((
        CASE WHEN "bool_col" THEN 1 ELSE 0 END
      ) AS DOUBLE PRECISION) / 1000
    ) * INTERVAL '1 SECOND'
  )
);

-- === SNOWFLAKE ===
TRY_CAST("str_int" AS DOUBLE);
TRY_CAST("str_float" AS DOUBLE);
CASE WHEN "bool_col" THEN 1 ELSE 0 END;
DATE_PART('epoch_second', "date_col") * 1000;
DATE_PART('epoch_millisecond', "timestamp_col");
"int_col";
"float_col";
TRY_CAST("str_date" AS TIMESTAMP);
TRY_CAST("str_datetime" AS TIMESTAMP);
TO_TIMESTAMP_TZ("epoch_ms", 3);
TO_TIMESTAMP_TZ(CASE WHEN "bool_col" THEN 1 ELSE 0 END, 3);
CAST("date_col" AS TIMESTAMP);
"timestamp_col";
DATE_PART('epoch_millisecond', TRY_CAST("str_date" AS TIMESTAMP));
TO_TIMESTAMP_TZ(CASE WHEN "bool_col" THEN 1 ELSE 0 END, 3);

-- === SPARK ===
CAST(`str_int` AS DOUBLE);
CAST(`str_float` AS DOUBLE);
CASE WHEN `bool_col` THEN 1 ELSE 0 END;
(
  UNIX_TIMESTAMP(FROM_UTC_TIMESTAMP(CAST(`date_col` AS TIMESTAMP), CURRENT_TIMEZONE())) * 1000 + CAST(EXTRACT(seconds FROM `date_col`) % 1 * 1000 AS BIGINT)
);
(
  UNIX_TIMESTAMP(FROM_UTC_TIMESTAMP(CAST(`timestamp_col` AS TIMESTAMP), CURRENT_TIMEZONE())) * 1000 + CAST(EXTRACT(seconds FROM `timestamp_col`) % 1 * 1000 AS BIGINT)
);
`int_col`;
`float_col`;
CAST(`str_date` AS TIMESTAMP);
CAST(`str_datetime` AS TIMESTAMP);
DATE_ADD(
  MILLISECOND,
  (
    `epoch_ms`
  ) % 1000,
  TO_UTC_TIMESTAMP(CAST(FROM_UNIXTIME((
    `epoch_ms`
  ) / 1000) AS TIMESTAMP), CURRENT_TIMEZONE())
);
DATE_ADD(
  MILLISECOND,
  (
    CASE WHEN `bool_col` THEN 1 ELSE 0 END
  ) % 1000,
  TO_UTC_TIMESTAMP(
    CAST(FROM_UNIXTIME((
      CASE WHEN `bool_col` THEN 1 ELSE 0 END
    ) / 1000) AS TIMESTAMP),
    CURRENT_TIMEZONE()
  )
);
CAST(`date_col` AS TIMESTAMP);
`timestamp_col`;
(
  UNIX_TIMESTAMP(FROM_UTC_TIMESTAMP(CAST(`str_date` AS TIMESTAMP), CURRENT_TIMEZONE())) * 1000 + CAST(EXTRACT(seconds FROM CAST(`str_date` AS TIMESTAMP)) % 1 * 1000 AS BIGINT)
);
DATE_ADD(
  MILLISECOND,
  (
    CASE WHEN `bool_col` THEN 1 ELSE 0 END
  ) % 1000,
  TO_UTC_TIMESTAMP(
    CAST(FROM_UNIXTIME((
      CASE WHEN `bool_col` THEN 1 ELSE 0 END
    ) / 1000) AS TIMESTAMP),
    CURRENT_TIMEZONE()
  )
);

-- === TRINO ===
TRY_CAST("str_int" AS DOUBLE);
TRY_CAST("str_float" AS DOUBLE);
CASE WHEN "bool_col" THEN 1 ELSE 0 END;
CAST(FLOOR(TO_UNIXTIME("date_col") * 1000) AS BIGINT);
CAST(FLOOR(TO_UNIXTIME("timestamp_col") * 1000) AS BIGINT);
"int_col";
"float_col";
TRY_CAST("str_date" AS TIMESTAMP);
TRY_CAST("str_datetime" AS TIMESTAMP);
WITH_TIMEZONE(
  DATE_ADD(
    'MILLISECOND',
    (
      (
        "epoch_ms"
      ) % 1000
    ),
    CAST(FROM_UNIXTIME(FLOOR(CAST(CAST("epoch_ms" AS BIGINT) AS DOUBLE) / 1000)) AS TIMESTAMP)
  ),
  'UTC'
);
WITH_TIMEZONE(
  DATE_ADD(
    'MILLISECOND',
    (
      (
        CASE WHEN "bool_col" THEN 1 ELSE 0 END
      ) % 1000
    ),
    CAST(FROM_UNIXTIME(
      FLOOR(CAST(CAST(CASE WHEN "bool_col" THEN 1 ELSE 0 END AS BIGINT) AS DOUBLE) / 1000)
    ) AS TIMESTAMP)
  ),
  'UTC'
);
CAST("date_col" AS TIMESTAMP);
"timestamp_col";
CAST(FLOOR(TO_UNIXTIME(TRY_CAST("str_date" AS TIMESTAMP)) * 1000) AS BIGINT);
WITH_TIMEZONE(
  DATE_ADD(
    'MILLISECOND',
    (
      (
        CASE WHEN "bool_col" THEN 1 ELSE 0 END
      ) % 1000
    ),
    CAST(FROM_UNIXTIME(
      FLOOR(CAST(CAST(CASE WHEN "bool_col" THEN 1 ELSE 0 END AS BIGINT) AS DOUBLE) / 1000)
    ) AS TIMESTAMP)
  ),
  'UTC'
);
