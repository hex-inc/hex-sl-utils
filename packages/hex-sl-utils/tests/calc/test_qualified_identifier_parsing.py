"""
Test parsing of qualified identifiers in calc expressions.

These tests verify that the calc parser correctly handles qualified column syntax
(dataset.column) including both valid and invalid forms.
"""

from typing import cast

import pytest

from hex_sl_utils.calc.ast.binary import BinaryBase
from hex_sl_utils.calc.ast.column import Column
from hex_sl_utils.calc.ast.functions import FuncBase
from hex_sl_utils.calc.parser import ParseError, parse_calc_expression


def test_parse_simple_qualified_identifier():
    """Test parsing simple qualified identifier."""
    expr = parse_calc_expression("carriers.Name")
    column = cast(Column, expr.root)

    # Verify the AST structure
    assert column.name == "Name"
    assert column.qualifiers == ("carriers",)

    # Verify string representation
    assert expr.to_string() == "carriers.Name"


def test_parse_unqualified_identifier():
    """Test parsing unqualified identifier (no dataset prefix)."""
    expr = parse_calc_expression("Name")
    column = cast(Column, expr.root)

    # Verify the AST structure
    assert column.name == "Name"
    assert column.qualifiers == ()

    # Verify string representation
    assert expr.to_string() == "Name"


def test_parse_qualified_identifier_with_backticks():
    """Test parsing qualified identifier with backtick-quoted parts."""
    expr = parse_calc_expression("`dataset name`.`column name`")
    column = cast(Column, expr.root)

    # Verify the AST structure
    assert column.name == "column name"
    assert column.qualifiers == ("dataset name",)

    # Verify string representation
    assert expr.to_string() == "`dataset name`.`column name`"


def test_parse_multiple_qualifiers():
    """Test parsing identifier with multiple qualifiers (though not typically used)."""
    # This tests the parser's ability to handle multiple dots
    # even though in practice we only use one level (dataset.column)
    expr = parse_calc_expression("a.b.c")
    column = cast(Column, expr.root)

    # The parser should treat this as dataset "a.b" and column "c"
    # based on the grammar rules
    assert column.name == "c"
    assert column.qualifiers == ("a", "b")

    # Verify string representation
    assert expr.to_string() == "a.b.c"


def test_parse_qualified_in_expression():
    """Test parsing qualified identifiers within larger expressions."""
    expr = parse_calc_expression("carriers.Name + ' - ' + Origin")
    binary = cast(BinaryBase, expr.root)

    # Verify the expression is a binary operation
    assert binary.binary == "+"

    # Check the left side (another binary operation)
    left = cast(BinaryBase, binary.lhs.root)
    left_column = cast(Column, left.lhs.root)
    assert left.binary == "+"
    assert left_column.name == "Name"
    assert left_column.qualifiers == ("carriers",)

    # Check the right side
    right_column = cast(Column, binary.rhs.root)
    assert right_column.name == "Origin"
    assert right_column.qualifiers == ()


def test_parse_qualified_in_function():
    """Test parsing qualified identifiers as function arguments."""
    expr = parse_calc_expression("upper(carriers.Name)")
    function = cast(FuncBase, expr.root)

    # Verify function structure
    assert function.fun == "upper"
    assert len(function.args.root) == 1

    # Check the argument
    arg = cast(Column, function.args.root[0].root)
    assert arg.name == "Name"
    assert arg.qualifiers == ("carriers",)


def test_parse_reserved_words_as_identifiers():
    """Test that reserved words can be used as identifiers when quoted."""
    # 'true' is a reserved word, but can be used as identifier with backticks
    expr = parse_calc_expression("`true`")
    column = cast(Column, expr.root)
    assert column.name == "true"
    assert column.qualifiers == ()

    # Same for qualified identifiers
    expr = parse_calc_expression("dataset.`false`")
    column = cast(Column, expr.root)
    assert column.name == "false"
    assert column.qualifiers == ("dataset",)


def test_malformed_qualified_identifier_starts_with_dot():
    """Test error handling for qualified identifier starting with dot."""
    with pytest.raises(ParseError) as exc_info:
        parse_calc_expression(".Name")

    # Verify we get a meaningful error message
    assert "expected" in str(exc_info.value).lower()


def test_malformed_qualified_identifier_ends_with_dot():
    """Test error handling for qualified identifier ending with dot."""
    with pytest.raises(ParseError) as exc_info:
        parse_calc_expression("carriers.")

    # Verify we get a meaningful error message
    assert "expected" in str(exc_info.value).lower()


def test_malformed_qualified_identifier_double_dot():
    """Test error handling for double dots in qualified identifier."""
    with pytest.raises(ParseError) as exc_info:
        parse_calc_expression("carriers..Name")

    # Verify we get a meaningful error message
    assert "expected" in str(exc_info.value).lower()


def test_empty_backticks():
    """Test error handling for empty backtick-quoted identifier."""
    with pytest.raises(ParseError) as exc_info:
        parse_calc_expression("``")

    # Empty backticks should not be allowed
    assert (
        "expected" in str(exc_info.value).lower()
        or "empty" in str(exc_info.value).lower()
    )


def test_parse_round_trip():
    """Test that parsing and converting back to string preserves the expression."""
    test_cases = [
        "carriers.Name",
        "Name",
        "`dataset name`.`column name`",
        "upper(carriers.Name)",
        "carriers.Name + Origin",
        "concat(carriers.Code, ' - ', aircraft.Manufacturer)",
        "carriers.Name || ' (' || carriers.Code || ')'",
    ]

    for expr_str in test_cases:
        expr = parse_calc_expression(expr_str)

        # Parse the string representation again
        reparsed = parse_calc_expression(expr.to_string())

        # Verify the ASTs are equal
        assert expr == reparsed, f"Round trip failed for: {expr_str}"
