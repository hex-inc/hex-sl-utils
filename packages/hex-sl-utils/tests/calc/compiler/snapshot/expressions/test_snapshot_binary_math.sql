-- === CALCS ===
-- int_col1 + int_col2
-- float_col + int_col2
-- int_col1 - int_col2
-- int_col1 * int_col2 * 2
-- int_col1 / int_col2
-- pow_base ^ pow_exp ^ 1
-- int_col1 % int_col2
-- (int_col1 + float_col) * (int_col2 - 1) / 2

-- === BIGQUERY ===
`int_col1` + `int_col2`;
`float_col` + `int_col2`;
`int_col1` - `int_col2`;
`int_col1` * `int_col2` * 2;
CASE WHEN `int_col2` = 0 THEN NULL ELSE ieee_divide(`int_col1`, `int_col2`) END;
POWER(`pow_base`, POWER(`pow_exp`, 1));
CASE
  WHEN `int_col2` = 0
  THEN NULL
  ELSE MOD(CAST(`int_col1` AS NUMERIC), CAST(`int_col2` AS NUMERIC))
END;
CASE
  WHEN 2 = 0
  THEN NULL
  ELSE ieee_divide((
    `int_col1` + `float_col`
  ) * (
    `int_col2` - 1
  ), 2)
END;

-- === CLICKHOUSE ===
"int_col1" + "int_col2";
"float_col" + "int_col2";
"int_col1" - "int_col2";
"int_col1" * "int_col2" * 2;
CASE WHEN "int_col2" = 0 THEN NULL ELSE "int_col1" / "int_col2" END;
POWER("pow_base", POWER("pow_exp", 1));
CASE WHEN "int_col2" = 0 THEN NULL ELSE "int_col1" % "int_col2" END;
CASE
  WHEN 2 = 0
  THEN NULL
  ELSE (
    "int_col1" + "float_col"
  ) * (
    "int_col2" - 1
  ) / 2
END;

-- === DUCKDB ===
"int_col1" + "int_col2";
"float_col" + "int_col2";
"int_col1" - "int_col2";
"int_col1" * "int_col2" * 2;
CASE WHEN "int_col2" = 0 THEN NULL ELSE "int_col1" / "int_col2" END;
POWER("pow_base", POWER("pow_exp", 1));
CASE WHEN "int_col2" = 0 THEN NULL ELSE "int_col1" % "int_col2" END;
CASE
  WHEN 2 = 0
  THEN NULL
  ELSE (
    "int_col1" + "float_col"
  ) * (
    "int_col2" - 1
  ) / 2
END;

-- === MSSQL ===
[int_col1] + [int_col2];
[float_col] + [int_col2];
[int_col1] - [int_col2];
[int_col1] * [int_col2] * 2;
CASE WHEN [int_col2] = 0 THEN NULL ELSE CAST([int_col1] AS FLOAT) / [int_col2] END;
POWER([pow_base], POWER([pow_exp], 1));
CASE WHEN [int_col2] = 0 THEN NULL ELSE [int_col1] % [int_col2] END;
CASE
  WHEN 2 = 0
  THEN NULL
  ELSE CAST((
    [int_col1] + [float_col]
  ) * (
    [int_col2] - 1
  ) AS FLOAT) / 2
END;

-- === MYSQL ===
`int_col1` + `int_col2`;
`float_col` + `int_col2`;
`int_col1` - `int_col2`;
`int_col1` * `int_col2` * 2;
CASE WHEN `int_col2` = 0 THEN NULL ELSE `int_col1` / `int_col2` END;
POWER(`pow_base`, POWER(`pow_exp`, 1));
CASE WHEN `int_col2` = 0 THEN NULL ELSE `int_col1` % `int_col2` END;
CASE
  WHEN 2 = 0
  THEN NULL
  ELSE (
    `int_col1` + `float_col`
  ) * (
    `int_col2` - 1
  ) / 2
END;

-- === POSTGRES ===
"int_col1" + "int_col2";
"float_col" + "int_col2";
"int_col1" - "int_col2";
"int_col1" * "int_col2" * 2;
CASE
  WHEN "int_col2" = 0
  THEN NULL
  ELSE CAST("int_col1" AS DOUBLE PRECISION) / "int_col2"
END;
POW("pow_base", POW("pow_exp", 1));
CASE WHEN "int_col2" = 0 THEN NULL ELSE "int_col1" % "int_col2" END;
CASE
  WHEN 2 = 0
  THEN NULL
  ELSE CAST((
    "int_col1" + "float_col"
  ) * (
    "int_col2" - 1
  ) AS DOUBLE PRECISION) / 2
END;

-- === REDSHIFT ===
"int_col1" + "int_col2";
"float_col" + "int_col2";
"int_col1" - "int_col2";
"int_col1" * "int_col2" * 2;
CASE
  WHEN "int_col2" = 0
  THEN NULL
  ELSE CAST("int_col1" AS DOUBLE PRECISION) / "int_col2"
END;
POWER("pow_base", POWER("pow_exp", 1));
CASE WHEN "int_col2" = 0 THEN NULL ELSE MOD("int_col1", "int_col2") END;
CASE
  WHEN 2 = 0
  THEN NULL
  ELSE CAST((
    "int_col1" + "float_col"
  ) * (
    "int_col2" - 1
  ) AS DOUBLE PRECISION) / 2
END;

-- === SNOWFLAKE ===
"int_col1" + "int_col2";
"float_col" + "int_col2";
"int_col1" - "int_col2";
"int_col1" * "int_col2" * 2;
CASE WHEN "int_col2" = 0 THEN NULL ELSE "int_col1" / "int_col2" END;
POWER("pow_base", POWER("pow_exp", 1));
CASE WHEN "int_col2" = 0 THEN NULL ELSE "int_col1" % "int_col2" END;
CASE
  WHEN 2 = 0
  THEN NULL
  ELSE (
    "int_col1" + "float_col"
  ) * (
    "int_col2" - 1
  ) / 2
END;

-- === SPARK ===
`int_col1` + `int_col2`;
`float_col` + `int_col2`;
`int_col1` - `int_col2`;
`int_col1` * `int_col2` * 2;
CASE WHEN `int_col2` = 0 THEN NULL ELSE `int_col1` / `int_col2` END;
POWER(`pow_base`, POWER(`pow_exp`, 1));
CASE WHEN `int_col2` = 0 THEN NULL ELSE `int_col1` % `int_col2` END;
CASE
  WHEN 2 = 0
  THEN NULL
  ELSE (
    `int_col1` + `float_col`
  ) * (
    `int_col2` - 1
  ) / 2
END;

-- === TRINO ===
"int_col1" + "int_col2";
"float_col" + "int_col2";
"int_col1" - "int_col2";
"int_col1" * "int_col2" * 2;
CASE WHEN "int_col2" = 0 THEN NULL ELSE CAST("int_col1" AS DOUBLE) / "int_col2" END;
POWER("pow_base", POWER("pow_exp", 1));
CASE WHEN "int_col2" = 0 THEN NULL ELSE "int_col1" % "int_col2" END;
CASE
  WHEN 2 = 0
  THEN NULL
  ELSE CAST((
    "int_col1" + "float_col"
  ) * (
    "int_col2" - 1
  ) AS DOUBLE) / 2
END;
