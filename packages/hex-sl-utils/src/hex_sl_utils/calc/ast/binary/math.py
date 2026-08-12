from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import Field

from hex_sl._vendor.sqlglot import exp
from hex_sl.calc.ast.binary.base import BinaryBase
from hex_sl.calc.parentheses import parens_if_needed
from hex_sl.datatype import DataType
from hex_sl.dialect.base import HexSLDialect
from hex_sl.expr import ExpressionKind, TypedSelectExpression
from hex_sl.utils import TypeCheckError

if TYPE_CHECKING:
    # This import seems to be needed to help mypy follow that the BinaryBase
    # lhs/rhs CalcExpr properties are available in child classes
    from hex_sl.calc.ast import CalcExpr  # noqa: F401


class BinaryMathBase(BinaryBase):
    """
    Base class for binary math operators
    """

    def _validate_math_operator_arg_types(
        self, left_type: DataType, right_type: DataType
    ) -> None:
        if left_type != DataType.NUMBER or right_type != DataType.NUMBER:
            msg = (
                f"Unsupported binary operator {self.get_op()} for data types "
                f"{left_type} and {right_type}"
            )
            raise TypeCheckError(msg)  # noqa: F821


class BinaryPlus(BinaryMathBase):
    binary: Literal["+"] = Field(
        default="+",
        description="Binary plus operator, as in 1 + 3 = 4",
        title="binary-plus-op",
    )

    def compile(
        self,
        left_expr: TypedSelectExpression,
        right_expr: TypedSelectExpression,
        dialect: HexSLDialect,
        timezone: str,
    ) -> TypedSelectExpression:
        self._validate_math_operator_arg_types(
            left_expr.data_type, right_expr.data_type
        )
        kind = ExpressionKind._validate_infer_kind([left_expr.kind, right_expr.kind])

        # Wrap operands in parentheses if needed based on precedence
        left = parens_if_needed(left_expr.expression, "+", operand_type="left")
        right = parens_if_needed(right_expr.expression, "+", operand_type="right")

        add_expr = exp.Add(this=left, expression=right)

        return TypedSelectExpression.from_sqlglot(add_expr, DataType.NUMBER, kind)


class BinaryMinus(BinaryMathBase):
    binary: Literal["-"] = Field(
        default="-",
        description="Binary minus operator, as in 5 - 3 = 2",
        title="binary-minus-op",
    )

    def compile(
        self,
        left_expr: TypedSelectExpression,
        right_expr: TypedSelectExpression,
        dialect: HexSLDialect,
        timezone: str,
    ) -> TypedSelectExpression:
        self._validate_math_operator_arg_types(
            left_expr.data_type, right_expr.data_type
        )
        kind = ExpressionKind._validate_infer_kind([left_expr.kind, right_expr.kind])

        # Wrap operands in parentheses if needed based on precedence
        left = parens_if_needed(left_expr.expression, "-", operand_type="left")
        right = parens_if_needed(right_expr.expression, "-", operand_type="right")

        sub_expr = exp.Sub(this=left, expression=right)

        return TypedSelectExpression.from_sqlglot(sub_expr, DataType.NUMBER, kind)


class BinaryMultiply(BinaryMathBase):
    binary: Literal["*"] = Field(
        default="*",
        description="Binary multiply operator, as in 2 * 3 = 6",
        title="binary-multiply-op",
    )

    def compile(
        self,
        left_expr: TypedSelectExpression,
        right_expr: TypedSelectExpression,
        dialect: HexSLDialect,
        timezone: str,
    ) -> TypedSelectExpression:
        self._validate_math_operator_arg_types(
            left_expr.data_type, right_expr.data_type
        )
        kind = ExpressionKind._validate_infer_kind([left_expr.kind, right_expr.kind])

        # Wrap operands in parentheses if needed based on precedence
        left = parens_if_needed(left_expr.expression, "*", operand_type="left")
        right = parens_if_needed(right_expr.expression, "*", operand_type="right")

        mul_expr = exp.Mul(this=left, expression=right)

        return TypedSelectExpression.from_sqlglot(mul_expr, DataType.NUMBER, kind)


class BinaryDivide(BinaryMathBase):
    binary: Literal["/"] = Field(
        default="/",
        description="Binary divide operator, as in 6 / 3 = 2",
        title="binary-divide-op",
    )

    def compile(
        self,
        left_expr: TypedSelectExpression,
        right_expr: TypedSelectExpression,
        dialect: HexSLDialect,
        timezone: str,
    ) -> TypedSelectExpression:
        self._validate_math_operator_arg_types(
            left_expr.data_type, right_expr.data_type
        )
        kind = ExpressionKind._validate_infer_kind([left_expr.kind, right_expr.kind])

        # Build condition: right == 0
        zero_literal = dialect.compile_literal(0)
        is_zero = TypedSelectExpression.from_sqlglot(
            exp.EQ(this=right_expr.expression, expression=zero_literal.expression),
            DataType.BOOLEAN,
            kind,
        )

        # Build division expression
        if dialect.truncates_on_integer_division():
            cast_left_expr = dialect.cast_to_float(left_expr)
            result_expr = dialect.build_division(cast_left_expr, right_expr)
        else:
            # Use dialect's build_division method
            result_expr = dialect.build_division(left_expr, right_expr)

        # Build NULL literal
        null_literal = dialect.build_null(DataType.NUMBER)

        # Use dialect's build_ifelse: if right == 0 then NULL else division
        return dialect.build_ifelse(is_zero, null_literal, result_expr)


class BinaryPower(BinaryMathBase):
    binary: Literal["^"] = Field(
        default="^",
        description="Binary power operator, as in 2 ^ 3 = 8",
        title="binary-power-op",
    )

    def compile(
        self,
        left_expr: TypedSelectExpression,
        right_expr: TypedSelectExpression,
        dialect: HexSLDialect,
        timezone: str,
    ) -> TypedSelectExpression:
        self._validate_math_operator_arg_types(
            left_expr.data_type, right_expr.data_type
        )
        kind = ExpressionKind._validate_infer_kind([left_expr.kind, right_expr.kind])

        # Wrap operands in parentheses if needed based on precedence
        left = parens_if_needed(left_expr.expression, "^", operand_type="left")
        right = parens_if_needed(right_expr.expression, "^", operand_type="right")

        pow_expr = exp.Pow(this=left, expression=right)

        return TypedSelectExpression.from_sqlglot(pow_expr, DataType.NUMBER, kind)


class BinaryModulus(BinaryMathBase):
    binary: Literal["%"] = Field(
        default="%",
        description="Binary modulus operator, as in 2 % 3 = 1",
        title="binary-modulus-op",
    )

    def compile(
        self,
        left_expr: TypedSelectExpression,
        right_expr: TypedSelectExpression,
        dialect: HexSLDialect,
        timezone: str,
    ) -> TypedSelectExpression:
        self._validate_math_operator_arg_types(
            left_expr.data_type, right_expr.data_type
        )
        kind = ExpressionKind._validate_infer_kind([left_expr.kind, right_expr.kind])

        # Build condition: right == 0
        zero_literal = dialect.compile_literal(0)
        is_zero = TypedSelectExpression.from_sqlglot(
            exp.EQ(this=right_expr.expression, expression=zero_literal.expression),
            DataType.BOOLEAN,
            kind,
        )

        # Build modulus expression
        if dialect.mod_supports_floats():
            # Wrap operands in parentheses if needed based on precedence
            left = parens_if_needed(left_expr.expression, "%", operand_type="left")
            right = parens_if_needed(right_expr.expression, "%", operand_type="right")
            mod_expr = exp.Mod(this=left, expression=right)
        else:
            # Cast to decimal for dialects that don't support float modulus
            left_decimal = exp.Cast(
                this=left_expr.expression, to=exp.DataType.build("DECIMAL")
            )
            right_decimal = exp.Cast(
                this=right_expr.expression, to=exp.DataType.build("DECIMAL")
            )
            # Wrap casted operands in parentheses if needed
            left = parens_if_needed(left_decimal, "%", operand_type="left")
            right = parens_if_needed(right_decimal, "%", operand_type="right")
            mod_expr = exp.Mod(this=left, expression=right)

        result_expr = TypedSelectExpression.from_sqlglot(
            mod_expr, DataType.NUMBER, kind
        )

        # Build NULL literal
        null_literal = dialect.build_null(DataType.NUMBER)

        # Use dialect's build_ifelse: if right == 0 then NULL else modulus
        return dialect.build_ifelse(is_zero, null_literal, result_expr)
