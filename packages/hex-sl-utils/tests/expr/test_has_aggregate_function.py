from hex_sl._vendor.sqlglot import parse_one
from hex_sl.expr import has_aggregate_function


def test_expression_with_aggregate():
    """Test that expressions with aggregate functions return True."""
    expression = parse_one("SELECT COUNT(a), SUM(b) FROM table1")
    assert has_aggregate_function(expression)


def test_expression_with_no_aggregate():
    """Test that expressions without aggregate functions return False."""
    expression = parse_one("SELECT a, b + 1 FROM table1")
    assert not has_aggregate_function(expression)


def test_simple_aggregate_function():
    """Test a simple aggregate function."""
    expression = parse_one("COUNT(*)")
    assert has_aggregate_function(expression)


def test_nested_aggregate():
    """Test nested expressions containing aggregates."""
    expression = parse_one("UPPER(COUNT(a))")
    assert has_aggregate_function(expression)


def test_window_function_without_aggregate():
    """Test window functions without aggregates."""
    expression = parse_one("ROW_NUMBER() OVER (ORDER BY a)")
    assert not has_aggregate_function(expression)
