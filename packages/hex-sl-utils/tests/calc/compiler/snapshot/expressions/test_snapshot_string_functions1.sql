-- === CALCS ===
-- concat()
-- concat(str_col1)
-- concat(str_col1, ' ', str_col2)
-- left(var_len_col, 2)
-- right(var_len_col, 2)
-- substitute(replace_col, 'cd', 'zz')
-- substitute('abcde', 'cd', 'zz')
-- lower(var_len_col)
-- upper(str_col2)

-- === BIGQUERY ===
'';
COALESCE(`str_col1`, '');
CONCAT(COALESCE(`str_col1`, ''), COALESCE(' ', ''), COALESCE(`str_col2`, ''));
LEFT(`var_len_col`, CAST(2 AS INT64));
RIGHT(`var_len_col`, CAST(2 AS INT64));
REPLACE(`replace_col`, 'cd', 'zz');
REPLACE('abcde', 'cd', 'zz');
LOWER(`var_len_col`);
UPPER(`str_col2`);

-- === CLICKHOUSE ===
'';
COALESCE("str_col1", '');
CONCAT(COALESCE("str_col1", ''), COALESCE(' ', ''), COALESCE("str_col2", ''));
LEFT("var_len_col", CAST(2 AS Nullable(Int32)));
RIGHT("var_len_col", CAST(2 AS Nullable(Int32)));
REPLACE("replace_col", 'cd', 'zz');
REPLACE('abcde', 'cd', 'zz');
LOWER("var_len_col");
UPPER("str_col2");

-- === DUCKDB ===
'';
CONCAT("str_col1");
CONCAT("str_col1", ' ', "str_col2");
LEFT("var_len_col", CAST(2 AS INT));
RIGHT("var_len_col", CAST(2 AS INT));
REPLACE("replace_col", 'cd', 'zz');
REPLACE('abcde', 'cd', 'zz');
LOWER("var_len_col");
UPPER("str_col2");

-- === MSSQL ===
'';
COALESCE([str_col1], '');
CONCAT([str_col1], ' ', [str_col2]);
LEFT([var_len_col], CAST(2 AS INTEGER));
RIGHT([var_len_col], CAST(2 AS INTEGER));
REPLACE([replace_col], 'cd', 'zz');
REPLACE('abcde', 'cd', 'zz');
LOWER([var_len_col]);
UPPER([str_col2]);

-- === MYSQL ===
'';
COALESCE(`str_col1`, '');
CONCAT_WS('', `str_col1`, ' ', `str_col2`);
LEFT(`var_len_col`, CAST(2 AS SIGNED));
RIGHT(`var_len_col`, CAST(2 AS SIGNED));
REPLACE(`replace_col`, 'cd', 'zz');
REPLACE('abcde', 'cd', 'zz');
LOWER(`var_len_col`);
UPPER(`str_col2`);

-- === POSTGRES ===
'';
CONCAT("str_col1");
CONCAT("str_col1", ' ', "str_col2");
LEFT("var_len_col", CAST(2 AS INT));
RIGHT("var_len_col", CAST(2 AS INT));
REPLACE("replace_col", 'cd', 'zz');
REPLACE('abcde', 'cd', 'zz');
LOWER("var_len_col");
UPPER("str_col2");

-- === REDSHIFT ===
CAST('' AS VARCHAR(MAX));
COALESCE("str_col1", '');
COALESCE("str_col1", '') || COALESCE(CAST(' ' AS VARCHAR(MAX)), '') || COALESCE("str_col2", '');
LEFT("var_len_col", CAST(2 AS INTEGER));
RIGHT("var_len_col", CAST(2 AS INTEGER));
REPLACE("replace_col", CAST('cd' AS VARCHAR(MAX)), CAST('zz' AS VARCHAR(MAX)));
REPLACE(
  CAST('abcde' AS VARCHAR(MAX)),
  CAST('cd' AS VARCHAR(MAX)),
  CAST('zz' AS VARCHAR(MAX))
);
LOWER("var_len_col");
UPPER("str_col2");

-- === SNOWFLAKE ===
'';
COALESCE("str_col1", '');
CONCAT(COALESCE("str_col1", ''), COALESCE(' ', ''), COALESCE("str_col2", ''));
LEFT("var_len_col", CAST(2 AS INT));
RIGHT("var_len_col", CAST(2 AS INT));
REPLACE("replace_col", 'cd', 'zz');
REPLACE('abcde', 'cd', 'zz');
LOWER("var_len_col");
UPPER("str_col2");

-- === SPARK ===
'';
COALESCE(`str_col1`, '');
CONCAT(COALESCE(`str_col1`, ''), COALESCE(' ', ''), COALESCE(`str_col2`, ''));
LEFT(`var_len_col`, CAST(2 AS INT));
RIGHT(`var_len_col`, CAST(2 AS INT));
REPLACE(`replace_col`, 'cd', 'zz');
REPLACE('abcde', 'cd', 'zz');
LOWER(`var_len_col`);
UPPER(`str_col2`);

-- === TRINO ===
'';
COALESCE("str_col1", '');
CONCAT(COALESCE("str_col1", ''), COALESCE(' ', ''), COALESCE("str_col2", ''));
SUBSTRING("var_len_col", 1, GREATEST(0, LEAST(CAST(2 AS INTEGER), LENGTH("var_len_col"))));
SUBSTRING(
  "var_len_col",
  LENGTH("var_len_col") - (
    GREATEST(0, LEAST(CAST(2 AS INTEGER), LENGTH("var_len_col"))) - 1
  )
);
REPLACE("replace_col", 'cd', 'zz');
REPLACE('abcde', 'cd', 'zz');
LOWER("var_len_col");
UPPER("str_col2");
