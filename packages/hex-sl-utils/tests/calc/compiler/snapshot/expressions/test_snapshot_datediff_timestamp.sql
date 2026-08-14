-- === CALCS ===
-- diffweeks(d1, d2)
-- diffdays(d1, d2)
-- diffhours(d1, d2)
-- diffminutes(d1, d2)
-- diffseconds(d1, d2)
-- diffmilliseconds(d1, d2)

-- === BIGQUERY ===
(
  IF(NOT `d2` IS NULL, UNIX_MILLIS(TIMESTAMP(`d2`)), NULL) - IF(NOT `d1` IS NULL, UNIX_MILLIS(TIMESTAMP(`d1`)), NULL)
) / 604800000.0;
(
  IF(NOT `d2` IS NULL, UNIX_MILLIS(TIMESTAMP(`d2`)), NULL) - IF(NOT `d1` IS NULL, UNIX_MILLIS(TIMESTAMP(`d1`)), NULL)
) / 86400000.0;
(
  IF(NOT `d2` IS NULL, UNIX_MILLIS(TIMESTAMP(`d2`)), NULL) - IF(NOT `d1` IS NULL, UNIX_MILLIS(TIMESTAMP(`d1`)), NULL)
) / 3600000.0;
(
  IF(NOT `d2` IS NULL, UNIX_MILLIS(TIMESTAMP(`d2`)), NULL) - IF(NOT `d1` IS NULL, UNIX_MILLIS(TIMESTAMP(`d1`)), NULL)
) / 60000.0;
(
  IF(NOT `d2` IS NULL, UNIX_MILLIS(TIMESTAMP(`d2`)), NULL) - IF(NOT `d1` IS NULL, UNIX_MILLIS(TIMESTAMP(`d1`)), NULL)
) / 1000.0;
(
  IF(NOT `d2` IS NULL, UNIX_MILLIS(TIMESTAMP(`d2`)), NULL) - IF(NOT `d1` IS NULL, UNIX_MILLIS(TIMESTAMP(`d1`)), NULL)
) / 1.0;

-- === CLICKHOUSE ===
(
  (
    toUnixTimestamp64Milli("d2")
  ) - (
    toUnixTimestamp64Milli("d1")
  )
) / 604800000.0;
(
  (
    toUnixTimestamp64Milli("d2")
  ) - (
    toUnixTimestamp64Milli("d1")
  )
) / 86400000.0;
(
  (
    toUnixTimestamp64Milli("d2")
  ) - (
    toUnixTimestamp64Milli("d1")
  )
) / 3600000.0;
(
  (
    toUnixTimestamp64Milli("d2")
  ) - (
    toUnixTimestamp64Milli("d1")
  )
) / 60000.0;
(
  (
    toUnixTimestamp64Milli("d2")
  ) - (
    toUnixTimestamp64Milli("d1")
  )
) / 1000.0;
(
  (
    toUnixTimestamp64Milli("d2")
  ) - (
    toUnixTimestamp64Milli("d1")
  )
) / 1.0;

-- === DUCKDB ===
(
  CAST(EPOCH_MS("d2") AS BIGINT) - CAST(EPOCH_MS("d1") AS BIGINT)
) / 604800000.0;
(
  CAST(EPOCH_MS("d2") AS BIGINT) - CAST(EPOCH_MS("d1") AS BIGINT)
) / 86400000.0;
(
  CAST(EPOCH_MS("d2") AS BIGINT) - CAST(EPOCH_MS("d1") AS BIGINT)
) / 3600000.0;
(
  CAST(EPOCH_MS("d2") AS BIGINT) - CAST(EPOCH_MS("d1") AS BIGINT)
) / 60000.0;
(
  CAST(EPOCH_MS("d2") AS BIGINT) - CAST(EPOCH_MS("d1") AS BIGINT)
) / 1000.0;
(
  CAST(EPOCH_MS("d2") AS BIGINT) - CAST(EPOCH_MS("d1") AS BIGINT)
) / 1.0;

-- === MSSQL ===
CAST((
  (
    (
      CAST(DATEDIFF(SECOND, CAST('1970-01-01 00:00:00' AS DATETIME2), CAST([d2] AS DATETIME2)) AS BIGINT) * 1000
    ) + DATEPART(millisecond, [d2])
  ) - (
    (
      CAST(DATEDIFF(SECOND, CAST('1970-01-01 00:00:00' AS DATETIME2), CAST([d1] AS DATETIME2)) AS BIGINT) * 1000
    ) + DATEPART(millisecond, [d1])
  )
) AS FLOAT) / 604800000.0;
CAST((
  (
    (
      CAST(DATEDIFF(SECOND, CAST('1970-01-01 00:00:00' AS DATETIME2), CAST([d2] AS DATETIME2)) AS BIGINT) * 1000
    ) + DATEPART(millisecond, [d2])
  ) - (
    (
      CAST(DATEDIFF(SECOND, CAST('1970-01-01 00:00:00' AS DATETIME2), CAST([d1] AS DATETIME2)) AS BIGINT) * 1000
    ) + DATEPART(millisecond, [d1])
  )
) AS FLOAT) / 86400000.0;
CAST((
  (
    (
      CAST(DATEDIFF(SECOND, CAST('1970-01-01 00:00:00' AS DATETIME2), CAST([d2] AS DATETIME2)) AS BIGINT) * 1000
    ) + DATEPART(millisecond, [d2])
  ) - (
    (
      CAST(DATEDIFF(SECOND, CAST('1970-01-01 00:00:00' AS DATETIME2), CAST([d1] AS DATETIME2)) AS BIGINT) * 1000
    ) + DATEPART(millisecond, [d1])
  )
) AS FLOAT) / 3600000.0;
CAST((
  (
    (
      CAST(DATEDIFF(SECOND, CAST('1970-01-01 00:00:00' AS DATETIME2), CAST([d2] AS DATETIME2)) AS BIGINT) * 1000
    ) + DATEPART(millisecond, [d2])
  ) - (
    (
      CAST(DATEDIFF(SECOND, CAST('1970-01-01 00:00:00' AS DATETIME2), CAST([d1] AS DATETIME2)) AS BIGINT) * 1000
    ) + DATEPART(millisecond, [d1])
  )
) AS FLOAT) / 60000.0;
CAST((
  (
    (
      CAST(DATEDIFF(SECOND, CAST('1970-01-01 00:00:00' AS DATETIME2), CAST([d2] AS DATETIME2)) AS BIGINT) * 1000
    ) + DATEPART(millisecond, [d2])
  ) - (
    (
      CAST(DATEDIFF(SECOND, CAST('1970-01-01 00:00:00' AS DATETIME2), CAST([d1] AS DATETIME2)) AS BIGINT) * 1000
    ) + DATEPART(millisecond, [d1])
  )
) AS FLOAT) / 1000.0;
CAST((
  (
    (
      CAST(DATEDIFF(SECOND, CAST('1970-01-01 00:00:00' AS DATETIME2), CAST([d2] AS DATETIME2)) AS BIGINT) * 1000
    ) + DATEPART(millisecond, [d2])
  ) - (
    (
      CAST(DATEDIFF(SECOND, CAST('1970-01-01 00:00:00' AS DATETIME2), CAST([d1] AS DATETIME2)) AS BIGINT) * 1000
    ) + DATEPART(millisecond, [d1])
  )
) AS FLOAT) / 1.0;

-- === MYSQL ===
(
  FLOOR(UNIX_TIMESTAMP(`d2`) * 1000) - FLOOR(UNIX_TIMESTAMP(`d1`) * 1000)
) / 604800000.0;
(
  FLOOR(UNIX_TIMESTAMP(`d2`) * 1000) - FLOOR(UNIX_TIMESTAMP(`d1`) * 1000)
) / 86400000.0;
(
  FLOOR(UNIX_TIMESTAMP(`d2`) * 1000) - FLOOR(UNIX_TIMESTAMP(`d1`) * 1000)
) / 3600000.0;
(
  FLOOR(UNIX_TIMESTAMP(`d2`) * 1000) - FLOOR(UNIX_TIMESTAMP(`d1`) * 1000)
) / 60000.0;
(
  FLOOR(UNIX_TIMESTAMP(`d2`) * 1000) - FLOOR(UNIX_TIMESTAMP(`d1`) * 1000)
) / 1000.0;
(
  FLOOR(UNIX_TIMESTAMP(`d2`) * 1000) - FLOOR(UNIX_TIMESTAMP(`d1`) * 1000)
) / 1.0;

-- === POSTGRES ===
CAST((
  CAST(FLOOR(EXTRACT('epoch' FROM "d2") * 1000) AS BIGINT) - CAST(FLOOR(EXTRACT('epoch' FROM "d1") * 1000) AS BIGINT)
) AS DOUBLE PRECISION) / 604800000.0;
CAST((
  CAST(FLOOR(EXTRACT('epoch' FROM "d2") * 1000) AS BIGINT) - CAST(FLOOR(EXTRACT('epoch' FROM "d1") * 1000) AS BIGINT)
) AS DOUBLE PRECISION) / 86400000.0;
CAST((
  CAST(FLOOR(EXTRACT('epoch' FROM "d2") * 1000) AS BIGINT) - CAST(FLOOR(EXTRACT('epoch' FROM "d1") * 1000) AS BIGINT)
) AS DOUBLE PRECISION) / 3600000.0;
CAST((
  CAST(FLOOR(EXTRACT('epoch' FROM "d2") * 1000) AS BIGINT) - CAST(FLOOR(EXTRACT('epoch' FROM "d1") * 1000) AS BIGINT)
) AS DOUBLE PRECISION) / 60000.0;
CAST((
  CAST(FLOOR(EXTRACT('epoch' FROM "d2") * 1000) AS BIGINT) - CAST(FLOOR(EXTRACT('epoch' FROM "d1") * 1000) AS BIGINT)
) AS DOUBLE PRECISION) / 1000.0;
CAST((
  CAST(FLOOR(EXTRACT('epoch' FROM "d2") * 1000) AS BIGINT) - CAST(FLOOR(EXTRACT('epoch' FROM "d1") * 1000) AS BIGINT)
) AS DOUBLE PRECISION) / 1.0;

-- === REDSHIFT ===
CAST((
  (
    (
      CAST(EXTRACT('millisecond' FROM "d2") AS BIGINT)
    ) + (
      CAST(EXTRACT('epoch' FROM "d2") AS BIGINT) * 1000
    )
  ) - (
    (
      CAST(EXTRACT('millisecond' FROM "d1") AS BIGINT)
    ) + (
      CAST(EXTRACT('epoch' FROM "d1") AS BIGINT) * 1000
    )
  )
) AS DOUBLE PRECISION) / 604800000.0;
CAST((
  (
    (
      CAST(EXTRACT('millisecond' FROM "d2") AS BIGINT)
    ) + (
      CAST(EXTRACT('epoch' FROM "d2") AS BIGINT) * 1000
    )
  ) - (
    (
      CAST(EXTRACT('millisecond' FROM "d1") AS BIGINT)
    ) + (
      CAST(EXTRACT('epoch' FROM "d1") AS BIGINT) * 1000
    )
  )
) AS DOUBLE PRECISION) / 86400000.0;
CAST((
  (
    (
      CAST(EXTRACT('millisecond' FROM "d2") AS BIGINT)
    ) + (
      CAST(EXTRACT('epoch' FROM "d2") AS BIGINT) * 1000
    )
  ) - (
    (
      CAST(EXTRACT('millisecond' FROM "d1") AS BIGINT)
    ) + (
      CAST(EXTRACT('epoch' FROM "d1") AS BIGINT) * 1000
    )
  )
) AS DOUBLE PRECISION) / 3600000.0;
CAST((
  (
    (
      CAST(EXTRACT('millisecond' FROM "d2") AS BIGINT)
    ) + (
      CAST(EXTRACT('epoch' FROM "d2") AS BIGINT) * 1000
    )
  ) - (
    (
      CAST(EXTRACT('millisecond' FROM "d1") AS BIGINT)
    ) + (
      CAST(EXTRACT('epoch' FROM "d1") AS BIGINT) * 1000
    )
  )
) AS DOUBLE PRECISION) / 60000.0;
CAST((
  (
    (
      CAST(EXTRACT('millisecond' FROM "d2") AS BIGINT)
    ) + (
      CAST(EXTRACT('epoch' FROM "d2") AS BIGINT) * 1000
    )
  ) - (
    (
      CAST(EXTRACT('millisecond' FROM "d1") AS BIGINT)
    ) + (
      CAST(EXTRACT('epoch' FROM "d1") AS BIGINT) * 1000
    )
  )
) AS DOUBLE PRECISION) / 1000.0;
CAST((
  (
    (
      CAST(EXTRACT('millisecond' FROM "d2") AS BIGINT)
    ) + (
      CAST(EXTRACT('epoch' FROM "d2") AS BIGINT) * 1000
    )
  ) - (
    (
      CAST(EXTRACT('millisecond' FROM "d1") AS BIGINT)
    ) + (
      CAST(EXTRACT('epoch' FROM "d1") AS BIGINT) * 1000
    )
  )
) AS DOUBLE PRECISION) / 1.0;

-- === SNOWFLAKE ===
(
  DATE_PART('epoch_millisecond', "d2") - DATE_PART('epoch_millisecond', "d1")
) / 604800000.0;
(
  DATE_PART('epoch_millisecond', "d2") - DATE_PART('epoch_millisecond', "d1")
) / 86400000.0;
(
  DATE_PART('epoch_millisecond', "d2") - DATE_PART('epoch_millisecond', "d1")
) / 3600000.0;
(
  DATE_PART('epoch_millisecond', "d2") - DATE_PART('epoch_millisecond', "d1")
) / 60000.0;
(
  DATE_PART('epoch_millisecond', "d2") - DATE_PART('epoch_millisecond', "d1")
) / 1000.0;
(
  DATE_PART('epoch_millisecond', "d2") - DATE_PART('epoch_millisecond', "d1")
) / 1.0;

-- === SPARK ===
(
  (
    UNIX_TIMESTAMP(FROM_UTC_TIMESTAMP(CAST(`d2` AS TIMESTAMP), CURRENT_TIMEZONE())) * 1000 + CAST(EXTRACT(seconds FROM `d2`) % 1 * 1000 AS BIGINT)
  ) - (
    UNIX_TIMESTAMP(FROM_UTC_TIMESTAMP(CAST(`d1` AS TIMESTAMP), CURRENT_TIMEZONE())) * 1000 + CAST(EXTRACT(seconds FROM `d1`) % 1 * 1000 AS BIGINT)
  )
) / 604800000.0;
(
  (
    UNIX_TIMESTAMP(FROM_UTC_TIMESTAMP(CAST(`d2` AS TIMESTAMP), CURRENT_TIMEZONE())) * 1000 + CAST(EXTRACT(seconds FROM `d2`) % 1 * 1000 AS BIGINT)
  ) - (
    UNIX_TIMESTAMP(FROM_UTC_TIMESTAMP(CAST(`d1` AS TIMESTAMP), CURRENT_TIMEZONE())) * 1000 + CAST(EXTRACT(seconds FROM `d1`) % 1 * 1000 AS BIGINT)
  )
) / 86400000.0;
(
  (
    UNIX_TIMESTAMP(FROM_UTC_TIMESTAMP(CAST(`d2` AS TIMESTAMP), CURRENT_TIMEZONE())) * 1000 + CAST(EXTRACT(seconds FROM `d2`) % 1 * 1000 AS BIGINT)
  ) - (
    UNIX_TIMESTAMP(FROM_UTC_TIMESTAMP(CAST(`d1` AS TIMESTAMP), CURRENT_TIMEZONE())) * 1000 + CAST(EXTRACT(seconds FROM `d1`) % 1 * 1000 AS BIGINT)
  )
) / 3600000.0;
(
  (
    UNIX_TIMESTAMP(FROM_UTC_TIMESTAMP(CAST(`d2` AS TIMESTAMP), CURRENT_TIMEZONE())) * 1000 + CAST(EXTRACT(seconds FROM `d2`) % 1 * 1000 AS BIGINT)
  ) - (
    UNIX_TIMESTAMP(FROM_UTC_TIMESTAMP(CAST(`d1` AS TIMESTAMP), CURRENT_TIMEZONE())) * 1000 + CAST(EXTRACT(seconds FROM `d1`) % 1 * 1000 AS BIGINT)
  )
) / 60000.0;
(
  (
    UNIX_TIMESTAMP(FROM_UTC_TIMESTAMP(CAST(`d2` AS TIMESTAMP), CURRENT_TIMEZONE())) * 1000 + CAST(EXTRACT(seconds FROM `d2`) % 1 * 1000 AS BIGINT)
  ) - (
    UNIX_TIMESTAMP(FROM_UTC_TIMESTAMP(CAST(`d1` AS TIMESTAMP), CURRENT_TIMEZONE())) * 1000 + CAST(EXTRACT(seconds FROM `d1`) % 1 * 1000 AS BIGINT)
  )
) / 1000.0;
(
  (
    UNIX_TIMESTAMP(FROM_UTC_TIMESTAMP(CAST(`d2` AS TIMESTAMP), CURRENT_TIMEZONE())) * 1000 + CAST(EXTRACT(seconds FROM `d2`) % 1 * 1000 AS BIGINT)
  ) - (
    UNIX_TIMESTAMP(FROM_UTC_TIMESTAMP(CAST(`d1` AS TIMESTAMP), CURRENT_TIMEZONE())) * 1000 + CAST(EXTRACT(seconds FROM `d1`) % 1 * 1000 AS BIGINT)
  )
) / 1.0;

-- === TRINO ===
CAST((
  CAST(FLOOR(TO_UNIXTIME("d2") * 1000) AS BIGINT) - CAST(FLOOR(TO_UNIXTIME("d1") * 1000) AS BIGINT)
) AS DOUBLE) / 604800000.0;
CAST((
  CAST(FLOOR(TO_UNIXTIME("d2") * 1000) AS BIGINT) - CAST(FLOOR(TO_UNIXTIME("d1") * 1000) AS BIGINT)
) AS DOUBLE) / 86400000.0;
CAST((
  CAST(FLOOR(TO_UNIXTIME("d2") * 1000) AS BIGINT) - CAST(FLOOR(TO_UNIXTIME("d1") * 1000) AS BIGINT)
) AS DOUBLE) / 3600000.0;
CAST((
  CAST(FLOOR(TO_UNIXTIME("d2") * 1000) AS BIGINT) - CAST(FLOOR(TO_UNIXTIME("d1") * 1000) AS BIGINT)
) AS DOUBLE) / 60000.0;
CAST((
  CAST(FLOOR(TO_UNIXTIME("d2") * 1000) AS BIGINT) - CAST(FLOOR(TO_UNIXTIME("d1") * 1000) AS BIGINT)
) AS DOUBLE) / 1000.0;
CAST((
  CAST(FLOOR(TO_UNIXTIME("d2") * 1000) AS BIGINT) - CAST(FLOOR(TO_UNIXTIME("d1") * 1000) AS BIGINT)
) AS DOUBLE) / 1.0;
