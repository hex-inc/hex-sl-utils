from __future__ import annotations

from datetime import datetime
from functools import lru_cache
from typing import Any, Union, cast

from lark import Token, Transformer

from hex_sl.calc.ast import CalcExpr
from hex_sl.calc.ast.args import Args
from hex_sl.calc.ast.binary import (
    BinaryAnd,
    BinaryDivide,
    BinaryEqual,
    BinaryGreater,
    BinaryGreaterEqual,
    BinaryLess,
    BinaryLessEqual,
    BinaryMinus,
    BinaryModulus,
    BinaryMultiply,
    BinaryNotEqual,
    BinaryOr,
    BinaryPlus,
    BinaryPower,
)
from hex_sl.calc.ast.column import Column
from hex_sl.calc.ast.functions import FuncConcat, func_for_name
from hex_sl.calc.ast.literals import (
    LiteralBool,
    LiteralDate,
    LiteralNull,
    LiteralNumber,
    LiteralString,
    LiteralTimestamp,
)
from hex_sl.calc.ast.parameter import Parameter
from hex_sl.calc.ast.unary import UnaryMinus, UnaryNot, UnaryPlus
from hex_sl.utils import UserFacingError

# Use the pre-compiled standalone parser (no grammar parsing at runtime)
from ._calc_parser_standalone import (
    Lark_StandAlone,
    UnexpectedCharacters,
    UnexpectedEOF,
    UnexpectedToken,
)


class ASTTransformer(Transformer[Token, CalcExpr]):
    """
    ASTTransformer is responsible for converting parsed tokens into an abstract
    syntax tree (AST) representation.

    Each method in this class corresponds to a specific grammar rule defined in
    `grammar.lark`. The methods are named after the rule names specified after the
    `->` arrow in the grammar file. For example, the rule
    `equality_expr ( "==" | "===" ) relational_expr -> binary_equal`
    in `grammar.lark` corresponds to the `binary_equal` method in this class.

    The methods take a list of parsed items (tokens or sub-expressions) and return a
    `CalcExpr` object that represents the corresponding AST node.
    """

    def binary_plus(self, items: list[CalcExpr]) -> CalcExpr:
        """
        Handles the addition operation.

        Args:
            items (list[CalcExpr]): The operands for the addition.

        Returns:
            CalcExpr: The resulting AST node for the addition operation.
        """
        return CalcExpr(root=BinaryPlus(lhs=items[0], rhs=items[1]))

    def binary_minus(self, items: list[CalcExpr]) -> CalcExpr:
        """
        Handles the subtraction operation.

        Args:
            items (list[CalcExpr]): The operands for the subtraction.

        Returns:
            CalcExpr: The resulting AST node for the subtraction operation.
        """
        return CalcExpr(root=BinaryMinus(lhs=items[0], rhs=items[1]))

    def binary_multiply(self, items: list[CalcExpr]) -> CalcExpr:
        """
        Handles the multiplication operation.

        Args:
            items (list[CalcExpr]): The operands for the multiplication.

        Returns:
            CalcExpr: The resulting AST node for the multiplication operation.
        """
        return CalcExpr(root=BinaryMultiply(lhs=items[0], rhs=items[1]))

    def binary_divide(self, items: list[CalcExpr]) -> CalcExpr:
        """
        Handles the division operation.

        Args:
            items (list[CalcExpr]): The operands for the division.

        Returns:
            CalcExpr: The resulting AST node for the division operation.
        """
        return CalcExpr(root=BinaryDivide(lhs=items[0], rhs=items[1]))

    def binary_modulus(self, items: list[CalcExpr]) -> CalcExpr:
        """
        Handles the modulus operation.

        Args:
            items (list[CalcExpr]): The operands for the modulus.

        Returns:
            CalcExpr: The resulting AST node for the modulus operation.
        """
        return CalcExpr(root=BinaryModulus(lhs=items[0], rhs=items[1]))

    def binary_power(self, items: list[CalcExpr]) -> CalcExpr:
        """
        Handles the power operation.

        Args:
            items (list[CalcExpr]): The operands for the power operation.

        Returns:
            CalcExpr: The resulting AST node for the power operation.
        """
        return CalcExpr(root=BinaryPower(lhs=items[0], rhs=items[1]))

    def binary_or(self, items: list[CalcExpr]) -> CalcExpr:
        """
        Handles the logical OR operation using `||`.

        Args:
            items (list[CalcExpr]): The operands for the OR operation.

        Returns:
            CalcExpr: The resulting AST node for the OR operation.
        """
        return CalcExpr(root=BinaryOr(lhs=items[0], rhs=items[1]))

    def binary_or_keyword(self, items: list[Union[CalcExpr, Token]]) -> CalcExpr:
        """
        Handles the logical OR operation using the `or` keyword.

        Args:
            items (list[Union[CalcExpr, Token]]): The operands for the OR operation.
                - items[0]: CalcExpr (left-hand side operand)
                - items[1]: Token (the "or" keyword operator)
                - items[2]: CalcExpr (right-hand side operand)

        Returns:
            CalcExpr: The resulting AST node for the OR operation.
        """
        # rhs uses items[2] because items[1] is the "or" keyword operator
        lhs = cast(CalcExpr, items[0])
        rhs = cast(CalcExpr, items[2])
        return CalcExpr(root=BinaryOr(lhs=lhs, rhs=rhs))

    def binary_and(self, items: list[CalcExpr]) -> CalcExpr:
        """
        Handles the logical AND operation using `&&`.

        Args:
            items (list[CalcExpr]): The operands for the AND operation.

        Returns:
            CalcExpr: The resulting AST node for the AND operation.
        """
        return CalcExpr(root=BinaryAnd(lhs=items[0], rhs=items[1]))

    def binary_and_keyword(self, items: list[Union[CalcExpr, Token]]) -> CalcExpr:
        """
        Handles the logical AND operation using the `and` keyword.

        Args:
            items (list[Union[CalcExpr, Token]]): The operands for the AND operation.
                - items[0]: CalcExpr (left-hand side operand)
                - items[1]: Token (the "and" keyword operator)
                - items[2]: CalcExpr (right-hand side operand)

        Returns:
            CalcExpr: The resulting AST node for the AND operation.
        """
        # rhs uses items[2] because items[1] is the "and" keyword operator
        lhs = cast(CalcExpr, items[0])
        rhs = cast(CalcExpr, items[2])
        return CalcExpr(root=BinaryAnd(lhs=lhs, rhs=rhs))

    def binary_less(self, items: list[CalcExpr]) -> CalcExpr:
        """
        Handles the less than operation.

        Args:
            items (list[CalcExpr]): The operands for the less than operation.

        Returns:
            CalcExpr: The resulting AST node for the less than operation.
        """
        return CalcExpr(root=BinaryLess(lhs=items[0], rhs=items[1]))

    def binary_less_equal(self, items: list[CalcExpr]) -> CalcExpr:
        """
        Handles the less than or equal to operation.

        Args:
            items (list[CalcExpr]): The operands for the less than or equal
            to operation.

        Returns:
            CalcExpr: The resulting AST node for the less than or equal to operation.
        """
        return CalcExpr(root=BinaryLessEqual(lhs=items[0], rhs=items[1]))

    def binary_greater(self, items: list[CalcExpr]) -> CalcExpr:
        """
        Handles the greater than operation.

        Args:
            items (list[CalcExpr]): The operands for the greater than operation.

        Returns:
            CalcExpr: The resulting AST node for the greater than operation.
        """
        return CalcExpr(root=BinaryGreater(lhs=items[0], rhs=items[1]))

    def binary_greater_equal(self, items: list[CalcExpr]) -> CalcExpr:
        """
        Handles the greater than or equal to operation.

        Args:
            items (list[CalcExpr]): The operands for the greater than or equal
            to operation.

        Returns:
            CalcExpr: The resulting AST node for the greater than or equal to operation.
        """
        return CalcExpr(root=BinaryGreaterEqual(lhs=items[0], rhs=items[1]))

    def binary_equal(self, items: list[CalcExpr]) -> CalcExpr:
        """
        Handles the equality comparison.

        Args:
            items (list[CalcExpr]): The operands for the equality comparison.

        Returns:
            CalcExpr: The resulting AST node for the equality comparison.
        """
        return CalcExpr(root=BinaryEqual(lhs=items[0], rhs=items[1]))

    def binary_not_equal(self, items: list[CalcExpr]) -> CalcExpr:
        """
        Handles the inequality comparison.

        Args:
            items (list[CalcExpr]): The operands for the inequality comparison.

        Returns:
            CalcExpr: The resulting AST node for the inequality comparison.
        """
        return CalcExpr(root=BinaryNotEqual(lhs=items[0], rhs=items[1]))

    def binary_concat(self, items: list[CalcExpr]) -> CalcExpr:
        """
        Handles the concatenation operation.

        Args:
            items (list[CalcExpr]): The operands for the concatenation.

        Returns:
            CalcExpr: The resulting AST node for the concatenation operation.
        """
        return CalcExpr(root=FuncConcat(args=Args(items)))

    def unary_minus(self, items: list[CalcExpr]) -> CalcExpr:
        """
        Handles the unary minus operation.

        Args:
            items (list[CalcExpr]): The operand for the unary minus operation.

        Returns:
            CalcExpr: The resulting AST node for the unary minus operation.
        """
        return CalcExpr(root=UnaryMinus(arg=items[0]))

    def unary_plus(self, items: list[CalcExpr]) -> CalcExpr:
        """
        Handles the unary plus operation.

        Args:
            items (list[CalcExpr]): The operand for the unary plus operation.

        Returns:
            CalcExpr: The resulting AST node for the unary plus operation.
        """
        return CalcExpr(root=UnaryPlus(arg=items[0]))

    def unary_not(self, items: list[CalcExpr]) -> CalcExpr:
        """
        Handles the unary NOT unary operation

        Args:
            items (list[CalcExpr]): The operand for the unary NOT operation.

        Returns:
            CalcExpr: The resulting AST node for the unary NOT operation.
        """
        return CalcExpr(root=UnaryNot(arg=items[0]))

    def unary_not_keyword(self, items: list[Union[Token, CalcExpr]]) -> CalcExpr:
        """
        Handles the unary NOT operation using the 'NOT' keyword.

        Args:
            items (list[Union[Token, CalcExpr]]): The operand for the NOT operation.
                - items[0]: Token (the "NOT" keyword operator)
                - items[1]: CalcExpr (the operand)

        Returns:
            CalcExpr: The resulting AST node for the unary NOT operation.
        """
        arg = cast(CalcExpr, items[1])
        return CalcExpr(root=UnaryNot(arg=arg))

    def literal_number(self, items: list[Token]) -> CalcExpr:
        """
        Handles the literal number.

        Args:
            items (list[Token]): The operand for the literal number.

        Returns:
            CalcExpr: The resulting AST node for the literal number.
        """
        str_value = items[0]
        if str_value.isdigit():
            literal = LiteralNumber(number=int(str_value))
        else:
            literal = LiteralNumber(number=float(str_value))
        return CalcExpr(root=literal)

    def literal_string(self, items: list[Token]) -> CalcExpr:
        """
        Handles the literal string.

        Args:
            items (list[Token]): The operand for the literal string.

        Returns:
            CalcExpr: The resulting AST node for the literal string.
        """
        # Remove quotes and unescape
        s = items[0][1:-1].encode("utf-8").decode("unicode_escape")
        return CalcExpr(root=LiteralString(str=s))

    def literal_date(self, items: list[Token]) -> CalcExpr:
        """
        Handles the literal date.

        Args:
            items (list[Token]): The operand for the literal date.

        Returns:
            CalcExpr: The resulting AST node for the literal date.
        """
        date_str = items[0][2:-1]  # Remove the d" and " parts
        return CalcExpr(
            root=LiteralDate(date=datetime.strptime(date_str, "%Y-%m-%d").date())
        )

    def literal_timestamp(self, items: list[Token]) -> CalcExpr:
        """
        Handles the literal timestamp.

        Args:
            items (list[Token]): The operand for the literal timestamp.

        Returns:
            CalcExpr: The resulting AST node for the literal timestamp.
        """
        timestamp_str = items[0][2:-1]  # Remove the t" and " parts
        try:
            # Try parsing with milliseconds
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S.%f")
        except ValueError:
            # If that fails, try without milliseconds
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S")
        return CalcExpr(root=LiteralTimestamp(timestamp=timestamp))

    def literal_bool(self, items: list[Token]) -> CalcExpr:
        """
        Handles the literal boolean.

        Args:
            items (list[Token]): The operand for the literal boolean.

        Returns:
            CalcExpr: The resulting AST node for the literal boolean.
        """
        return CalcExpr(root=LiteralBool(bool=items[0].lower() == "true"))

    def literal_null(self, items: list[Token]) -> CalcExpr:
        """
        Handles the literal null.

        Args:
            items (list[Token]): The operand for the literal null.

        Returns:
            CalcExpr: The resulting AST node for the literal null.
        """
        return CalcExpr(root=LiteralNull(position=items[0].start_pos))

    def column(self, items: list[Token]) -> CalcExpr:
        """
        Handles the column reference.

        Args:
            items (list[Token]): The operand for the column reference.

        Returns:
            CalcExpr: The resulting AST node for the column reference.
        """
        column_name = items[0][1:-1] if items[0].startswith("`") else items[0]
        return CalcExpr(root=Column(name=column_name))

    def identifier(self, items: list[Token]) -> CalcExpr:
        """
        Handles identifiers.

        Args:
            items (list[Token]): The operand for the identifier.

        Returns:
            CalcExpr: The resulting AST node for the identifier.
        """
        return CalcExpr(root=Column(name=items[0]))

    def qualified_identifier(self, items: list[Token]) -> list[str]:
        """
        Handles the qualified_identifier rule to extract all parts.

        Args:
            items (list[Token]): The tokens from the qualified_identifier rule.

        Returns:
            list[str]: List of identifier parts.
        """
        parts = []
        for item in items:
            if hasattr(item, "type") and item.type in ("IDENTIFIER", "COLUMN"):
                part = str(item.value) if hasattr(item, "value") else str(item)
                if part.startswith("`") and part.endswith("`"):
                    part = part[1:-1]
                parts.append(part)
        return parts

    def qualified_column(self, items: list[list[str]]) -> CalcExpr:
        """
        Handles qualified column references (e.g., dataset.column).
        Called when grammar matches: qualified_identifier -> qualified_column

        Args:
            items (list[list[str]]): Contains the list of parts from
                qualified_identifier.

        Returns:
            CalcExpr: The resulting AST node for the qualified column reference.
        """
        # items[0] is the list of parts from qualified_identifier
        parts = items[0]

        # Last part is the column name, preceding parts are qualifiers
        column_name = parts[-1]
        qualifiers = tuple(parts[:-1])

        return CalcExpr(root=Column(name=column_name, qualifiers=qualifiers))

    def parameter(self, items: list[Token]) -> CalcExpr:
        """
        Handles the parameter.

        Args:
            items (list[Token]): The token containing the parameter.

        Returns:
            CalcExpr: The resulting AST node for the parameter.
        """
        # Remove {{ }} and strip whitespace
        param_name = items[0][2:-2].strip()
        return CalcExpr(root=Parameter(parameter=param_name))

    def function_call(self, items: list[Union[Token, CalcExpr]]) -> CalcExpr:
        """
        Handles the function call.

        Args:
            items (list[Union[Token, CalcExpr]]): The operand for the function call.

        Returns:
            CalcExpr: The resulting AST node for the function call.
        """
        func_name = cast(Token, items[0]).lower()
        args = Args(root=[item for item in items[1:] if isinstance(item, CalcExpr)])

        func_cls = func_for_name(func_name)

        func = func_cls(args=args)
        assert (
            # avg has several aliases, so handle specially here
            func.fun == func_name or func.fun == "avg"
        ), f"Function name {func.fun} does not match {func_name}"

        return CalcExpr(root=func)


_parser = Lark_StandAlone(transformer=ASTTransformer())  # type: ignore[no-untyped-call]


@lru_cache(maxsize=1024)
def parse_calc_expression(expression: str) -> CalcExpr:
    """
    Parses a Calc Language expression and returns the corresponding AST node.

    Args:
        expression (str): The Calc Language expression to parse.

    Returns:
        CalcExpr: The resulting AST node for the expression.

    Raises:
        ParseError: If there is an error parsing the expression.
    """
    try:
        # From the docstring of parser.parse:
        #   Returns:
        #       If a transformer is supplied to ``__init__``, returns whatever is the
        #       result of the transformation. Otherwise, returns a Tree instance.
        #
        # So this returns a CalcExpr instance in our case since we provide the
        # ASTTransformer to the Lark constructor. Unfortunately, the type signature of
        # the parse method does not handle this case. So we explicitly cast the result
        # to CalcExpr.
        expr: Any = _parser.parse(expression)
        return cast(CalcExpr, expr)
    except UnexpectedToken as e:
        context = e.get_context(expression)
        message = (
            f"Unexpected token at line {e.line}, column {e.column}.\n"
            f"Expected one of: {', '.join(e.expected)}\n"
            f"Context: {context}"
        )
        raise ParseError(message) from e
    except UnexpectedCharacters as e:
        context = e.get_context(expression)
        message = (
            f"Unexpected character at line {e.line}, column {e.column}.\n"
            f"Expected one of: {', '.join(e.allowed)}\n"
            f"Context: {context}"
        )
        raise ParseError(message) from e
    except UnexpectedEOF as e:
        context = e.get_context(expression)
        message = (
            f"Unexpected end of input at line {e.line}, column {e.column}.\n"
            f"Expected one of: {', '.join(e.expected)}\n"
            f"Context: {context}"
        )
        raise ParseError(message) from e


class ParseError(UserFacingError):
    """
    Exception raised when there is an error parsing a Calc Language expression.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
