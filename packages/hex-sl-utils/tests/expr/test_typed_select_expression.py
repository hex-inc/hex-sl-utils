"""Tests for TypedSelectExpression validation."""

import pytest
from hex_sl._vendor.sqlglot import parse_one
from hex_sl.datatype import DataType
from hex_sl.expr import TypedSelectExpression
from hex_sl_common.exceptions import TypeCheckError
from inline_snapshot import snapshot


# Test data for valid expressions
VALID_EXPRESSIONS = [
    # Simple expressions
    ("'test'", DataType.STRING),
    ("col1", DataType.NUMBER),
    ("NULL", DataType.NULL),
    ("TRUE", DataType.BOOLEAN),
    ("FALSE", DataType.BOOLEAN),
    ("42.5", DataType.NUMBER),
    ("-123", DataType.NUMBER),
    # Binary expressions
    ("a + 1", DataType.NUMBER),
    ("a - b", DataType.NUMBER),
    ("x * 2.5", DataType.NUMBER),
    ("total / count", DataType.NUMBER),
    ("a = 5", DataType.BOOLEAN),
    ("x > 10", DataType.BOOLEAN),
    ("y < 100", DataType.BOOLEAN),
    ("price >= 50.0", DataType.BOOLEAN),
    ("quantity <= 1000", DataType.BOOLEAN),
    ("status != 'cancelled'", DataType.BOOLEAN),
    ("first_name || ' ' || last_name", DataType.STRING),
    # Parenthesized expressions
    ("(a + b)", DataType.NUMBER),
    ("(a + b) * (c - d)", DataType.NUMBER),
    ("((x + y) * z)", DataType.NUMBER),
    # BETWEEN expressions
    ("age BETWEEN 18 AND 65", DataType.BOOLEAN),
    ("price NOT BETWEEN 10.0 AND 100.0", DataType.BOOLEAN),
    ("date_col BETWEEN '2024-01-01' AND '2024-12-31'", DataType.BOOLEAN),
    # Bracket (array/map access) expressions
    ("array_col[0]", DataType.STRING),
    ("matrix[i][j]", DataType.NUMBER),
    ("json_data['key']", DataType.STRING),
    # CASE expressions
    (
        """
        CASE
            WHEN x > 0 THEN 'positive'
            WHEN x < 0 THEN 'negative'
            ELSE 'zero'
        END
    """,
        DataType.STRING,
    ),
    (
        """
        CASE status
            WHEN 'active' THEN 1
            WHEN 'pending' THEN 2
            ELSE 0
        END
    """,
        DataType.NUMBER,
    ),
    (
        """
        CASE
            WHEN score >= 90 THEN 'A'
            WHEN score >= 80 THEN 'B'
            WHEN score >= 70 THEN 'C'
            ELSE 'F'
        END
    """,
        DataType.STRING,
    ),
    # CAST expressions
    ("CAST('123' AS INT)", DataType.NUMBER),
    ("CAST(123.45 AS VARCHAR)", DataType.STRING),
    ("CAST('2024-01-01' AS DATE)", DataType.DATE),
    ("'2024-01-01'::DATE", DataType.DATE),
    ("'123'::INTEGER", DataType.NUMBER),
    ("123::TEXT", DataType.STRING),
    # IN expressions
    ("status IN ('active', 'pending', 'approved')", DataType.BOOLEAN),
    ("category NOT IN (1, 2, 3)", DataType.BOOLEAN),
    ("city IN ('New York', 'Los Angeles', 'Chicago')", DataType.BOOLEAN),
    # Function calls
    ("ROUND(price, 2)", DataType.NUMBER),
    ("UPPER(name)", DataType.STRING),
    ("LOWER(email)", DataType.STRING),
    ("LENGTH(description)", DataType.NUMBER),
    ("TRIM(comment)", DataType.STRING),
    ("ABS(difference)", DataType.NUMBER),
    ("COALESCE(value1, value2, 0)", DataType.NUMBER),
    ("NULLIF(a, b)", DataType.NUMBER),
    ("GREATEST(x, y, z)", DataType.NUMBER),
    ("LEAST(a, b, c)", DataType.NUMBER),
    # Date/time functions
    ("DATE_TRUNC('month', created_at)", DataType.TIMESTAMP),
    ("DATE_PART('year', birth_date)", DataType.NUMBER),
    ("EXTRACT(MONTH FROM order_date)", DataType.NUMBER),
    ("CURRENT_DATE", DataType.DATE),
    ("CURRENT_TIMESTAMP", DataType.TIMESTAMP),
    # Aggregate functions
    ("SUM(amount)", DataType.NUMBER),
    ("AVG(price)", DataType.NUMBER),
    ("COUNT(*)", DataType.NUMBER),
    ("COUNT(DISTINCT user_id)", DataType.NUMBER),
    ("MAX(salary)", DataType.NUMBER),
    ("MIN(age)", DataType.NUMBER),
    ("STRING_AGG(name, ', ')", DataType.STRING),
    # Window functions
    ("SUM(amount) OVER (PARTITION BY category ORDER BY date)", DataType.NUMBER),
    ("ROW_NUMBER() OVER (PARTITION BY dept ORDER BY salary DESC)", DataType.NUMBER),
    ("RANK() OVER (ORDER BY score DESC)", DataType.NUMBER),
    ("LAG(value, 1) OVER (ORDER BY timestamp)", DataType.NUMBER),
    ("LEAD(price, 1, 0) OVER (ORDER BY date)", DataType.NUMBER),
    # Unary expressions
    ("-amount", DataType.NUMBER),
    ("NOT is_active", DataType.BOOLEAN),
    ("+value", DataType.NUMBER),
    # Date arithmetic
    ("created_at + INTERVAL '1 day'", DataType.TIMESTAMP),
    ("end_date - start_date", DataType.NUMBER),
    ("NOW() - INTERVAL '30 minutes'", DataType.TIMESTAMP),
    # Complex nested expressions
    ("SUBSTRING(email FROM 1 FOR POSITION('@' IN email) - 1)", DataType.STRING),
    ("price * (1 + tax_rate) * (1 - COALESCE(discount_rate, 0))", DataType.NUMBER),
    (
        """
        (a + b) *
        CASE
            WHEN c > 0 THEN 2
            WHEN c < 0 THEN -1
            ELSE 1
        END +
        COALESCE(d, 0)
    """,
        DataType.NUMBER,
    ),
    (
        """
        ROUND(
            AVG(
                CASE
                    WHEN status = 'complete' THEN amount * 1.1
                    ELSE amount * 0.9
                END
            ),
            2
        )
    """,
        DataType.NUMBER,
    ),
]


@pytest.mark.parametrize("expr_str,expected_type", VALID_EXPRESSIONS)
def test_valid_expressions(expr_str, expected_type):
    """Test that valid SQL expressions are accepted."""
    expr = parse_one(expr_str, dialect="duckdb")
    result = TypedSelectExpression.from_sqlglot(expr, expected_type, strict=True)
    assert result.expression == expr
    assert result.data_type == expected_type


def test_invalid_subquery():
    """Test that subqueries are rejected."""
    # Scalar subquery
    expr = parse_one("(SELECT MAX(x) FROM table)", dialect="duckdb")

    with pytest.raises(TypeCheckError) as exc_info:
        TypedSelectExpression.from_sqlglot(expr, DataType.NUMBER, strict=True)

    assert str(exc_info.value) == snapshot(
        "Expected an expression compatible inside a SELECT, found Subquery"
    )


def test_invalid_subquery_in_expression():
    """Test that subqueries within expressions are rejected."""
    # IN with subquery
    expr = parse_one("x IN (SELECT id FROM users)", dialect="duckdb")

    with pytest.raises(TypeCheckError) as exc_info:
        TypedSelectExpression.from_sqlglot(expr, DataType.BOOLEAN, strict=True)

    assert str(exc_info.value) == snapshot("""\
Found 4 invalid sub-expression(s) in the expression tree.
Invalid expressions:
  - Subquery: (SELECT id FROM users)
  - Select: SELECT id FROM users
  - From: FROM users
  - Table: users\
""")


def test_invalid_table_reference():
    """Test that table references are rejected."""
    # Import exp to create a Table node directly
    from hex_sl._vendor.sqlglot import exp

    table = exp.Table(this="my_table")

    with pytest.raises(TypeCheckError) as exc_info:
        TypedSelectExpression.from_sqlglot(table, DataType.STRING, strict=True)

    assert str(exc_info.value) == snapshot(
        "Expected an expression compatible inside a SELECT, found Table"
    )


def test_invalid_alias_at_top_level():
    """Test that aliases are rejected at the top level."""
    from hex_sl._vendor.sqlglot import exp

    alias = exp.Alias(this=exp.Column(this="col1"), alias="c1")

    with pytest.raises(TypeCheckError) as exc_info:
        TypedSelectExpression.from_sqlglot(alias, DataType.STRING, strict=True)

    assert str(exc_info.value) == snapshot(
        "Expected an expression compatible inside a SELECT, found Alias"
    )


def test_nested_invalid_expression():
    """Test that invalid expressions nested deep in the tree are caught."""
    # CASE with EXISTS subquery
    expr = parse_one(
        """
        CASE
            WHEN EXISTS(SELECT 1 FROM table WHERE x = y) THEN 1
            ELSE 0
        END
        """,
        dialect="duckdb",
    )

    with pytest.raises(TypeCheckError) as exc_info:
        TypedSelectExpression.from_sqlglot(expr, DataType.NUMBER, strict=True)

    assert str(exc_info.value) == snapshot("""\
Found 4 invalid sub-expression(s) in the expression tree.
Invalid expressions:
  - Select: SELECT 1 FROM table WHERE x = y
  - From: FROM table
  - Where: WHERE x = y
  - Table: table\
""")


def test_invalid_cte_reference():
    """Test that CTEs are rejected."""
    expr = parse_one(
        """
        WITH cte AS (SELECT 1 as val)
        SELECT val FROM cte
        """,
        dialect="duckdb",
    )

    # The entire WITH statement is invalid
    with pytest.raises(TypeCheckError) as exc_info:
        TypedSelectExpression.from_sqlglot(expr, DataType.NUMBER, strict=True)

    assert str(exc_info.value) == snapshot(
        "Expected an expression compatible inside a SELECT, found Select"
    )
