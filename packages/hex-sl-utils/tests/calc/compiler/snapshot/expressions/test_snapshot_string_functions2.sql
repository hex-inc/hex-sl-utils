-- === CALCS ===
-- length(var_len_col)
-- contains(var_len_col, 'BC')
-- startswith(var_len_col, 'ABC')
-- endswith(replace_col, 'de')

-- === BIGQUERY ===
LENGTH(`var_len_col`);
INSTR(`var_len_col`, 'BC') > 0;
STARTS_WITH(`var_len_col`, 'ABC');
ENDS_WITH(`replace_col`, 'de');

-- === CLICKHOUSE ===
CHAR_LENGTH("var_len_col");
position("var_len_col", 'BC') <> 0;
startsWith("var_len_col", 'ABC');
endsWith("replace_col", 'de');

-- === DUCKDB ===
LENGTH("var_len_col");
CONTAINS("var_len_col", 'BC');
STARTS_WITH("var_len_col", 'ABC');
SUFFIX("replace_col", 'de');

-- === MSSQL ===
LEN(CONCAT('A', [var_len_col], 'Z')) - 2;
IIF(CHARINDEX('BC', [var_len_col]) > 0, 1, 0);
IIF(LEFT([var_len_col], LEN('ABC')) = 'ABC', 1, 0);
IIF(RIGHT([replace_col], LEN('de')) = 'de', 1, 0);

-- === MYSQL ===
CHAR_LENGTH(`var_len_col`);
LOCATE('BC', `var_len_col`) > 0;
LEFT(`var_len_col`, CHAR_LENGTH('ABC')) = 'ABC';
RIGHT(`replace_col`, CHAR_LENGTH('de')) = 'de';

-- === POSTGRES ===
LENGTH("var_len_col");
POSITION('BC' IN "var_len_col") > 0;
STARTS_WITH("var_len_col", 'ABC');
RIGHT("replace_col", LENGTH('de')) = 'de';

-- === REDSHIFT ===
LENGTH("var_len_col");
POSITION(CAST('BC' AS VARCHAR(MAX)) IN "var_len_col") > 0;
LEFT("var_len_col", LENGTH(CAST('ABC' AS VARCHAR(MAX)))) = CAST('ABC' AS VARCHAR(MAX));
RIGHT("replace_col", LENGTH(CAST('de' AS VARCHAR(MAX)))) = CAST('de' AS VARCHAR(MAX));

-- === SNOWFLAKE ===
LENGTH("var_len_col");
CONTAINS("var_len_col", 'BC');
STARTSWITH("var_len_col", 'ABC');
ENDSWITH("replace_col", 'de');

-- === SPARK ===
LENGTH(`var_len_col`);
CONTAINS(`var_len_col`, 'BC');
STARTSWITH(`var_len_col`, 'ABC');
ENDSWITH(`replace_col`, 'de');

-- === TRINO ===
LENGTH("var_len_col");
STRPOS("var_len_col", 'BC') > 0;
STARTS_WITH("var_len_col", 'ABC');
SUBSTRING("replace_col", -LENGTH('de')) = 'de';
