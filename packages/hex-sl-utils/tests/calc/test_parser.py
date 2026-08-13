from datetime import datetime

import pytest
from hex_sl.calc.ast.binary import (
    BinaryAnd,
    BinaryDivide,
    BinaryMinus,
    BinaryModulus,
    BinaryMultiply,
    BinaryOr,
    BinaryPlus,
    BinaryPower,
)
from hex_sl.calc.ast.unary import UnaryMinus, UnaryNot, UnaryPlus
from hex_sl.calc.ast.literals import (
    LiteralBool,
    LiteralDate,
    LiteralNull,
    LiteralNumber,
    LiteralString,
    LiteralTimestamp,
)
from hex_sl.calc.ast.column import Column
from hex_sl.calc.ast.functions import FuncConcat, FuncLeft, FuncSin, FuncSqrt
from hex_sl.calc.ast.parameter import Parameter

from hex_sl.calc.parser import ParseError, parse_calc_expression
from hex_sl.utils import UserFacingError
from inline_snapshot import snapshot


# Literal tests
def test_literal_number():
    expression = "42"
    ast = parse_calc_expression(expression).root
    assert isinstance(ast, LiteralNumber)
    assert ast.number_value == snapshot(42)


def test_literal_bool():
    expression = "true"
    ast = parse_calc_expression(expression).root
    assert isinstance(ast, LiteralBool)
    assert ast.bool_value == snapshot(True)


def test_literal_null():
    expression = "null"
    ast = parse_calc_expression(expression).root
    assert isinstance(ast, LiteralNull)


# Literal string tests
def test_literal_string_double_quotes():
    expression = '"hello"'
    ast = parse_calc_expression(expression).root
    assert isinstance(ast, LiteralString)
    assert ast.str_value == snapshot("hello")


def test_literal_string_single_quotes():
    expression = "'hello'"
    ast = parse_calc_expression(expression).root
    assert isinstance(ast, LiteralString)
    assert ast.str_value == snapshot("hello")


def test_literal_string_with_double_quotes_and_escape_characters():
    expression = '"hello\\nworld"'
    ast = parse_calc_expression(expression).root
    assert isinstance(ast, LiteralString)
    assert ast.str_value == snapshot(
        """\
hello
world\
"""
    )


def test_literal_string_with_single_quotes_and_escape_characters():
    expression = "'hello\\nworld'"
    ast = parse_calc_expression(expression).root
    assert isinstance(ast, LiteralString)
    assert ast.str_value == snapshot(
        """\
hello
world\
"""
    )


def test_literal_string_with_quotes_inside():
    expression = '"He said, \\"Hello!\\""'
    ast = parse_calc_expression(expression).root
    assert isinstance(ast, LiteralString)
    assert ast.str_value == snapshot('He said, "Hello!"')


def test_literal_string_with_single_quotes_inside():
    expression = "'It\\'s a test'"
    ast = parse_calc_expression(expression).root
    assert isinstance(ast, LiteralString)
    assert ast.str_value == snapshot("It's a test")


# Literal date and timestamp tests
def test_literal_date():
    expression = 'd"2023-06-01"'
    ast = parse_calc_expression(expression).root
    assert isinstance(ast, LiteralDate)
    assert ast.date_value == datetime.strptime("2023-06-01", "%Y-%m-%d").date()
    expected_string = snapshot('d"2023-06-01"')
    assert ast.to_string() == expected_string


def test_literal_timestamp():
    expression = 't"2023-06-01T12:34:56"'
    ast = parse_calc_expression(expression).root
    assert isinstance(ast, LiteralTimestamp)
    assert ast.timestamp_value == datetime.strptime(
        "2023-06-01T12:34:56", "%Y-%m-%dT%H:%M:%S"
    )
    expected_string = snapshot('t"2023-06-01T12:34:56"')
    assert ast.to_string() == expected_string


def test_literal_timestamp_with_milliseconds():
    expression = 't"2023-06-01T12:34:56.789"'
    ast = parse_calc_expression(expression).root
    assert isinstance(ast, LiteralTimestamp)
    assert ast.timestamp_value == datetime.strptime(
        "2023-06-01T12:34:56.789", "%Y-%m-%dT%H:%M:%S.%f"
    )
    expected_string = snapshot('t"2023-06-01T12:34:56.789"')
    assert ast.to_string() == expected_string


# Binary operation tests
def test_binary_plus():
    expression = "1 + 2"
    ast = parse_calc_expression(expression).root
    assert isinstance(ast, BinaryPlus)
    assert isinstance(ast.lhs.root, LiteralNumber)
    assert ast.lhs.root.number_value == 1
    assert isinstance(ast.rhs.root, LiteralNumber)
    assert ast.rhs.root.number_value == 2


def test_binary_minus():
    expression = "3 - 4"
    ast = parse_calc_expression(expression).root
    assert isinstance(ast, BinaryMinus)
    assert isinstance(ast.lhs.root, LiteralNumber)
    assert ast.lhs.root.number_value == 3
    assert isinstance(ast.rhs.root, LiteralNumber)
    assert ast.rhs.root.number_value == 4


def test_binary_multiply():
    expression = "5 * 6"
    ast = parse_calc_expression(expression).root
    assert isinstance(ast, BinaryMultiply)
    assert isinstance(ast.lhs.root, LiteralNumber)
    assert ast.lhs.root.number_value == 5
    assert isinstance(ast.rhs.root, LiteralNumber)
    assert ast.rhs.root.number_value == 6


def test_binary_divide():
    expression = "8 / 4"
    ast = parse_calc_expression(expression).root
    assert isinstance(ast, BinaryDivide)
    assert isinstance(ast.lhs.root, LiteralNumber)
    assert ast.lhs.root.number_value == 8
    assert isinstance(ast.rhs.root, LiteralNumber)
    assert ast.rhs.root.number_value == 4


def test_binary_modulus():
    expression = "9 % 4"
    ast = parse_calc_expression(expression).root
    assert isinstance(ast, BinaryModulus)
    assert isinstance(ast.lhs.root, LiteralNumber)
    assert ast.lhs.root.number_value == 9
    assert isinstance(ast.rhs.root, LiteralNumber)
    assert ast.rhs.root.number_value == 4


def test_binary_power():
    expression = "2 ^ 3"
    ast = parse_calc_expression(expression).root
    assert isinstance(ast, BinaryPower)
    assert isinstance(ast.lhs.root, LiteralNumber)
    assert ast.lhs.root.number_value == 2
    assert isinstance(ast.rhs.root, LiteralNumber)
    assert ast.rhs.root.number_value == 3


def test_binary_and():
    expression = "true && false"
    ast = parse_calc_expression(expression).root
    assert isinstance(ast, BinaryAnd)
    assert isinstance(ast.lhs.root, LiteralBool)
    assert ast.lhs.root.bool_value is True
    assert isinstance(ast.rhs.root, LiteralBool)
    assert ast.rhs.root.bool_value is False


def test_binary_or():
    expression = "true || false"
    ast = parse_calc_expression(expression).root
    assert isinstance(ast, BinaryOr)
    assert isinstance(ast.lhs.root, LiteralBool)
    assert ast.lhs.root.bool_value is True
    assert isinstance(ast.rhs.root, LiteralBool)
    assert ast.rhs.root.bool_value is False


# Unary operation tests
def test_unary_minus():
    expression = "-5"
    ast = parse_calc_expression(expression).root
    assert isinstance(ast, UnaryMinus)
    assert isinstance(ast.arg.root, LiteralNumber)
    assert ast.arg.root.number_value == 5


def test_unary_plus():
    expression = "+5"
    ast = parse_calc_expression(expression).root
    assert isinstance(ast, UnaryPlus)
    assert isinstance(ast.arg.root, LiteralNumber)
    assert ast.arg.root.number_value == 5


def test_unary_not():
    expression = "!true"
    ast = parse_calc_expression(expression).root
    assert isinstance(ast, UnaryNot)
    assert isinstance(ast.arg.root, LiteralBool)
    assert ast.arg.root.bool_value is True


@pytest.mark.parametrize("not_keyword", ["NOT", "not", "NoT"])
def test_unary_not_keyword(not_keyword):
    expression = f"{not_keyword} true"
    ast = parse_calc_expression(expression).root
    assert isinstance(ast, UnaryNot)
    assert isinstance(ast.arg.root, LiteralBool)
    assert ast.arg.root.bool_value is True


def test_case_insensitive_and():
    expression = "true AND false"
    ast = parse_calc_expression(expression).root
    assert isinstance(ast, BinaryAnd)
    assert isinstance(ast.lhs.root, LiteralBool)
    assert ast.lhs.root.bool_value is True
    assert isinstance(ast.rhs.root, LiteralBool)
    assert ast.rhs.root.bool_value is False


# Validation tests
def test_invalid_expression():
    with pytest.raises(ParseError):
        parse_calc_expression("23 34")


# Operator precedence tests
def test_operator_precedence_addition_multiplication():
    expression = "1 + 2 * 3"
    ast = parse_calc_expression(expression).root
    assert ast.to_string() == snapshot("(1 + (2 * 3))")


def test_operator_precedence_multiplication_addition():
    expression = "2 * 3 + 1"
    ast = parse_calc_expression(expression).root
    assert ast.to_string() == snapshot("((2 * 3) + 1)")


def test_operator_precedence_subtraction_division():
    expression = "10 - 4 / 2"
    ast = parse_calc_expression(expression).root
    assert ast.to_string() == snapshot("(10 - (4 / 2))")


def test_operator_precedence_division_subtraction():
    expression = "8 / 4 - 2"
    ast = parse_calc_expression(expression).root
    assert ast.to_string() == snapshot("((8 / 4) - 2)")


def test_operator_precedence_combined():
    expression = "1 + 2 * 3 - 4 / 2"
    ast = parse_calc_expression(expression).root
    assert ast.to_string() == snapshot("((1 + (2 * 3)) - (4 / 2))")


def test_operator_precedence_power_multiplication():
    expression = "2 ^ 3 * 4"
    ast = parse_calc_expression(expression).root
    assert ast.to_string() == snapshot("((2 ^ 3) * 4)")


def test_operator_precedence_multiplication_power():
    expression = "2 * 3 ^ 4"
    ast = parse_calc_expression(expression).root
    assert ast.to_string() == snapshot("(2 * (3 ^ 4))")


def test_operator_precedence_power_addition():
    expression = "2 ^ 3 + 4"
    ast = parse_calc_expression(expression).root
    assert ast.to_string() == snapshot("((2 ^ 3) + 4)")


def test_operator_precedence_addition_power():
    expression = "2 + 3 ^ 4"
    ast = parse_calc_expression(expression).root
    assert ast.to_string() == snapshot("(2 + (3 ^ 4))")


# Column tests
def test_column_backticks():
    expression = "`MyColumn`"
    ast = parse_calc_expression(expression).root
    assert isinstance(ast, Column)
    assert ast.name == "MyColumn"
    assert ast.to_string() == snapshot("MyColumn")


def test_column_with_spaces_backticks():
    expression = "`My Column`"
    ast = parse_calc_expression(expression).root
    assert isinstance(ast, Column)
    assert ast.name == "My Column"
    assert ast.to_string() == snapshot("`My Column`")


def test_column_identifier():
    expression = "MyColumn"
    ast = parse_calc_expression(expression).root
    assert isinstance(ast, Column)
    assert ast.name == "MyColumn"
    assert ast.to_string() == snapshot("MyColumn")


def test_column_backticks_with_keywords():
    expression = "`true`"
    ast = parse_calc_expression(expression).root
    assert isinstance(ast, Column)
    assert ast.name == "true"
    assert ast.to_string() == snapshot("`true`")


# Qualified column tests
def test_qualified_column_simple():
    expression = "dataset.column"
    ast = parse_calc_expression(expression).root
    assert isinstance(ast, Column)
    assert ast.name == "column"
    assert ast.qualifiers == ("dataset",)
    assert ast.to_string() == snapshot("dataset.column")


def test_qualified_column_with_backticks():
    expression = "`dataset`.`column`"
    ast = parse_calc_expression(expression).root
    assert isinstance(ast, Column)
    assert ast.name == "column"
    assert ast.qualifiers == ("dataset",)
    assert ast.to_string() == snapshot("dataset.column")


def test_qualified_column_mixed_quoting():
    expression = "dataset.`column name`"
    ast = parse_calc_expression(expression).root
    assert isinstance(ast, Column)
    assert ast.name == "column name"
    assert ast.qualifiers == ("dataset",)
    assert ast.to_string() == snapshot("dataset.`column name`")


def test_qualified_column_dataset_with_spaces():
    expression = "`dataset name`.column"
    ast = parse_calc_expression(expression).root
    assert isinstance(ast, Column)
    assert ast.name == "column"
    assert ast.qualifiers == ("dataset name",)
    assert ast.to_string() == snapshot("`dataset name`.column")


def test_qualified_column_multi_level():
    expression = "schema.dataset.column"
    ast = parse_calc_expression(expression).root
    assert isinstance(ast, Column)
    assert ast.name == "column"
    assert ast.qualifiers == ("schema", "dataset")
    assert ast.to_string() == snapshot("schema.dataset.column")


def test_qualified_column_multi_level_with_spaces():
    expression = "`my schema`.`my dataset`.`my column`"
    ast = parse_calc_expression(expression).root
    assert isinstance(ast, Column)
    assert ast.name == "my column"
    assert ast.qualifiers == ("my schema", "my dataset")
    assert ast.to_string() == snapshot("`my schema`.`my dataset`.`my column`")


def test_qualified_column_with_keywords():
    expression = "`true`.`false`"
    ast = parse_calc_expression(expression).root
    assert isinstance(ast, Column)
    assert ast.name == "false"
    assert ast.qualifiers == ("true",)
    assert ast.to_string() == snapshot("`true`.`false`")


# Function call tests
def test_function_call_sin():
    expression = "sin(23)"
    ast = parse_calc_expression(expression).root
    assert isinstance(ast, FuncSin)
    assert len(ast.args.root) == 1
    assert isinstance(ast.args.root[0].root, LiteralNumber)
    assert ast.args.root[0].root.number_value == 23
    assert ast.to_string() == snapshot("sin(23)")


def test_function_call_sqrt():
    expression = "Sqrt(4)"
    ast = parse_calc_expression(expression).root
    assert isinstance(ast, FuncSqrt)
    assert len(ast.args.root) == 1
    assert isinstance(ast.args.root[0].root, LiteralNumber)
    assert ast.args.root[0].root.number_value == 4
    assert ast.to_string() == snapshot("sqrt(4)")


def test_function_call_multiple_args():
    expression = "bogus(45, 1)"
    with pytest.raises(UserFacingError, match="Unknown function: bogus"):
        parse_calc_expression(expression)


def test_function_call_concat():
    expression = "concat('hello', ' ', 'world')"
    ast = parse_calc_expression(expression).root
    assert isinstance(ast, FuncConcat)
    assert len(ast.args.root) == 3
    assert isinstance(ast.args.root[0].root, LiteralString)
    assert ast.args.root[0].root.str_value == "hello"
    assert isinstance(ast.args.root[1].root, LiteralString)
    assert ast.args.root[1].root.str_value == " "
    assert isinstance(ast.args.root[2].root, LiteralString)
    assert ast.args.root[2].root.str_value == "world"
    assert ast.to_string() == snapshot('concat("hello", " ", "world")')


def test_concat_operator():
    expression = '"Hello" & " World"'
    ast = parse_calc_expression(expression).root
    assert isinstance(ast, FuncConcat)
    assert len(ast.args.root) == 2
    assert isinstance(ast.args.root[0].root, LiteralString)
    assert ast.args.root[0].root.str_value == "Hello"
    assert isinstance(ast.args.root[1].root, LiteralString)
    assert ast.args.root[1].root.str_value == " World"
    assert ast.to_string() == snapshot('concat("Hello", " World")')


def test_function_call_left():
    expression = "left('hello', 3)"
    ast = parse_calc_expression(expression).root
    assert isinstance(ast, FuncLeft)
    assert len(ast.args.root) == 2
    assert ast.to_string() == snapshot('left("hello", 3)')


# Scientific notation tests
@pytest.mark.parametrize(
    "expression, expected",
    [
        ("1e10", 1e10),
        ("1E10", 1e10),
        ("1.5e3", 1500),
        ("1.5E3", 1500),
        ("1e-5", 1e-5),
        ("1E-5", 1e-5),
        ("3.14e+2", 314),
        ("3.14E+2", 314),
    ],
)
def test_scientific_notation(expression, expected):
    ast = parse_calc_expression(expression).root
    assert isinstance(ast, LiteralNumber)
    assert ast.number_value == expected


def test_scientific_notation_in_expression():
    expression = "1e3 + 2.5e-2"
    ast = parse_calc_expression(expression).root
    assert ast.to_string() == snapshot("(1000 + 0.025)")


def test_scientific_notation_with_multiplication():
    expression = "2e3 * 3e-2"
    ast = parse_calc_expression(expression).root
    assert ast.to_string() == snapshot("(2000 * 0.03)")


def test_scientific_notation_in_function():
    expression = "round(1.23e-4, 2)"
    ast = parse_calc_expression(expression).root
    assert ast.to_string() == snapshot("round(0.000123, 2)")


def test_invalid_scientific_notation():
    with pytest.raises(ParseError):
        parse_calc_expression("1e")
    with pytest.raises(ParseError):
        parse_calc_expression("1.5e3.5")


def test_identifiers_with_keyword_substrings():
    expressions = ["null_coll", "order_by", "android", "notebook", "truefalse"]
    for expr in expressions:
        ast = parse_calc_expression(expr).root
        assert isinstance(ast, Column)
        assert ast.name == expr


# Parameter tests
def test_parameter_simple():
    expression = "{{foo}}"
    ast = parse_calc_expression(expression).root
    assert isinstance(ast, Parameter)
    assert ast.parameter == "foo"
    assert ast.to_string() == snapshot("{{foo}}")


def test_parameter_with_spaces():
    expression = "{{ bar   }}"
    ast = parse_calc_expression(expression).root
    assert isinstance(ast, Parameter)
    assert ast.parameter == "bar"
    assert ast.to_string() == snapshot("{{bar}}")


def test_parameter_in_expression():
    expression = "1 + {{baz}} * 2"
    ast = parse_calc_expression(expression).root
    assert ast.to_string() == snapshot("(1 + ({{baz}} * 2))")


def test_parameter_in_function():
    expression = "sin({{angle}})"
    ast = parse_calc_expression(expression).root
    assert ast.to_string() == snapshot("sin({{angle}})")


# Complex expression tests with qualified columns
def test_qualified_column_in_binary_expression():
    expression = "orders.total + customers.discount"
    ast = parse_calc_expression(expression).root
    assert isinstance(ast, BinaryPlus)
    assert isinstance(ast.lhs.root, Column)
    assert ast.lhs.root.name == "total"
    assert ast.lhs.root.qualifiers == ("orders",)
    assert isinstance(ast.rhs.root, Column)
    assert ast.rhs.root.name == "discount"
    assert ast.rhs.root.qualifiers == ("customers",)
    assert ast.to_string() == snapshot("(orders.total + customers.discount)")


def test_qualified_column_with_function():
    expression = "sum(sales.revenue) / count(sales.id)"
    ast = parse_calc_expression(expression).root
    assert ast.to_string() == snapshot("(sum(sales.revenue) / count(sales.id))")


def test_qualified_column_complex_expression():
    expression = "`sales data`.revenue * (1 - `sales data`.`discount rate`)"
    ast = parse_calc_expression(expression).root
    assert ast.to_string() == snapshot(
        "(`sales data`.revenue * (1 - `sales data`.`discount rate`))"
    )


def test_parse_stringify_roundtrip():
    """Test that parsing and stringifying produces the same result."""
    test_cases = [
        "column",
        "dataset.column",
        "`dataset`.`column`",
        "a.b.c",
        "`my dataset`.`my column`",
        "orders.total + customers.discount",
        "sum(sales.revenue) / count(sales.id)",
    ]

    for expr in test_cases:
        parsed = parse_calc_expression(expr)
        stringified = parsed.to_string()
        reparsed = parse_calc_expression(stringified)

        # Check that the parsed and reparsed expressions are equal
        assert parsed == reparsed, f"Roundtrip failed for: {expr}"
