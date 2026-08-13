from hex_sl._vendor.sqlglot import parse_one
from hex_sl.expr import has_column_references


def test_expression_with_columns():
    """Test that expressions with column references return True."""
    expression = parse_one("SELECT table1.a, table1.b FROM table1")
    assert has_column_references(expression)


def test_expression_with_no_columns():
    """Test that expressions without column references return False."""
    expression = parse_one("SELECT 1, 'hello', 42.5")
    assert not has_column_references(expression)


def test_simple_column_reference():
    """Test a simple column reference."""
    expression = parse_one("a")
    assert has_column_references(expression)


def test_arithmetic_with_columns():
    """Test arithmetic expressions containing columns."""
    expression = parse_one("a + b * 2")
    assert has_column_references(expression)


def test_functions_without_columns():
    """Test function calls without column references."""
    expression = parse_one("UPPER('hello')")
    assert not has_column_references(expression)
