"""
Test parsing of qualified identifiers in calc expressions.

These tests verify that the calc parser correctly handles qualified column syntax
(dataset.column) including both valid and invalid forms.
"""

import pytest

from hex_sl_utils.calc.parser import ParseError, parse_calc_expression


def test_parse_simple_qualified_identifier():
    """Test parsing simple qualified identifier."""
    expr = parse_calc_expression("carriers.Name")

    # Verify the AST structure
    assert expr.root.name == "Name"
    assert expr.root.qualifiers == ("carriers",)

    # Verify string representation
    assert expr.to_string() == "carriers.Name"


def test_parse_unqualified_identifier():
    """Test parsing unqualified identifier (no dataset prefix)."""
    expr = parse_calc_expression("Name")

    # Verify the AST structure
    assert expr.root.name == "Name"
    assert expr.root.qualifiers == ()

    # Verify string representation
    assert expr.to_string() == "Name"


def test_parse_qualified_identifier_with_backticks():
    """Test parsing qualified identifier with backtick-quoted parts."""
    expr = parse_calc_expression("`dataset name`.`column name`")

    # Verify the AST structure
    assert expr.root.name == "column name"
    assert expr.root.qualifiers == ("dataset name",)

    # Verify string representation
    assert expr.to_string() == "`dataset name`.`column name`"


def test_parse_multiple_qualifiers():
    """Test parsing identifier with multiple qualifiers (though not typically used)."""
    # This tests the parser's ability to handle multiple dots
    # even though in practice we only use one level (dataset.column)
    expr = parse_calc_expression("a.b.c")

    # The parser should treat this as dataset "a.b" and column "c"
    # based on the grammar rules
    assert expr.root.name == "c"
    assert expr.root.qualifiers == ("a", "b")

    # Verify string representation
    assert expr.to_string() == "a.b.c"


def test_parse_qualified_in_expression():
    """Test parsing qualified identifiers within larger expressions."""
    expr = parse_calc_expression("carriers.Name + ' - ' + Origin")

    # Verify the expression is a binary operation
    assert expr.root.binary == "+"

    # Check the left side (another binary operation)
    left = expr.root.lhs.root
    assert left.binary == "+"
    assert left.lhs.root.name == "Name"
    assert left.lhs.root.qualifiers == ("carriers",)

    # Check the right side
    assert expr.root.rhs.root.name == "Origin"
    assert expr.root.rhs.root.qualifiers == ()


def test_parse_qualified_in_function():
    """Test parsing qualified identifiers as function arguments."""
    expr = parse_calc_expression("upper(carriers.Name)")

    # Verify function structure
    assert expr.root.fun == "upper"
    assert len(expr.root.args.root) == 1

    # Check the argument
    arg = expr.root.args.root[0].root
    assert arg.name == "Name"
    assert arg.qualifiers == ("carriers",)


def test_parse_reserved_words_as_identifiers():
    """Test that reserved words can be used as identifiers when quoted."""
    # 'true' is a reserved word, but can be used as identifier with backticks
    expr = parse_calc_expression("`true`")
    assert expr.root.name == "true"
    assert expr.root.qualifiers == ()

    # Same for qualified identifiers
    expr = parse_calc_expression("dataset.`false`")
    assert expr.root.name == "false"
    assert expr.root.qualifiers == ("dataset",)


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
