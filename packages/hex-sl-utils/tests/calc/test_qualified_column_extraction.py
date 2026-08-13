"""
Test qualified column extraction from calc expressions.

These tests verify that calc expressions can identify cross-dataset column references
using the qualified column syntax (dataset.column).
"""

from hex_sl_utils.calc.parser import parse_calc_expression
from hex_sl_utils.dialect.duckdb import DuckDB


def test_single_qualified_column():
    """Test extraction of a single qualified column reference."""
    expr = parse_calc_expression("carriers.Name")
    qualified_cols = expr.get_all_columns(DuckDB())

    expected = [(("carriers",), "Name")]
    assert qualified_cols == expected


def test_multiple_qualified_columns():
    """Test extraction of multiple qualified column references."""
    expr = parse_calc_expression("carriers.Name + aircraft.Year_Built")
    qualified_cols = expr.get_all_columns(DuckDB())

    expected = [(("aircraft",), "Year_Built"), (("carriers",), "Name")]
    assert qualified_cols == expected


def test_mixed_qualified_unqualified():
    """Test expressions with both qualified and unqualified columns."""
    expr = parse_calc_expression("origin + carriers.Name")
    qualified_cols = expr.get_all_columns(DuckDB())

    expected = [
        ((), "origin"),  # Unqualified
        (("carriers",), "Name"),  # Qualified
    ]
    assert qualified_cols == expected


def test_nested_qualified_columns():
    """Test qualified columns in nested expressions."""
    expr = parse_calc_expression("upper(concat(origin, '-', carriers.Name))")
    qualified_cols = expr.get_all_columns(DuckDB())

    expected = [
        ((), "origin"),
        (("carriers",), "Name"),
    ]
    assert qualified_cols == expected


def test_qualified_columns_in_aggregates():
    """Test qualified columns within aggregate functions."""
    expr = parse_calc_expression("sum(carriers.Carrier_Count)")
    qualified_cols = expr.get_all_columns(DuckDB())

    expected = [(("carriers",), "Carrier_Count")]
    assert qualified_cols == expected


def test_complex_cross_dataset_expression():
    """Test complex expression with multiple cross-dataset references."""
    expr = parse_calc_expression("if(carriers.Name = 'United', aircraft.Year_Built, 0)")
    qualified_cols = expr.get_all_columns(DuckDB())

    expected = [(("aircraft",), "Year_Built"), (("carriers",), "Name")]
    assert qualified_cols == expected


def test_no_qualified_columns():
    """Test expression with only unqualified columns."""
    expr = parse_calc_expression("origin + destination")
    qualified_cols = expr.get_all_columns(DuckDB())

    expected = [((), "destination"), ((), "origin")]
    assert qualified_cols == expected


def test_literals_and_parameters():
    """Test that literals and parameters don't appear in qualified columns."""
    expr = parse_calc_expression("carriers.Name + 'suffix' + {{my_parameter}}")
    qualified_cols = expr.get_all_columns(DuckDB())

    expected = [(("carriers",), "Name")]
    assert qualified_cols == expected


def test_method_exists():
    """Verify that get_all_columns method exists on CalcExpr."""
    expr = parse_calc_expression("carriers.Name")
    assert hasattr(expr, "get_all_columns")
    assert callable(expr.get_all_columns)
