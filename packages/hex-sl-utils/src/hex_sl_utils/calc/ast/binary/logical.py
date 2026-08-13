# pyright: reportIncompatibleVariableOverride=false

from __future__ import annotations

from typing import Literal

from pydantic import Field

from hex_sl_utils._vendor.sqlglot import exp
from hex_sl_utils.calc.ast.binary import BinaryBase
from hex_sl_utils.calc.parentheses import parens_if_needed
from hex_sl_utils.datatype import DataType
from hex_sl_utils.dialect.dialect import Dialect
from hex_sl_utils.exception import TypeCheckError
from hex_sl_utils.expr import ExpressionKind, TypedSelectExpression


class BinaryLogicalBase(BinaryBase):
    """
    Base class for binary logical operators
    """

    def _validate_logical_operator_arg_types(
        self,
        left_type: DataType,
        right_type: DataType,
    ) -> None:
        if left_type != DataType.BOOLEAN or right_type != DataType.BOOLEAN:
            msg = (
                f"Unsupported binary operator {self.get_op()} for data types "
                f"{left_type} and {right_type}"
            )
            raise TypeCheckError(msg)


class BinaryOr(BinaryLogicalBase):
    binary: Literal["||"] = Field(
        default="||",
        description="Binary OR operator, as in true || false = true",
        title="binary-or-op",
    )

    def compile(
        self,
        left_expr: TypedSelectExpression,
        right_expr: TypedSelectExpression,
        dialect: Dialect,
        timezone: str,
    ) -> TypedSelectExpression:
        self._validate_logical_operator_arg_types(
            left_expr.data_type, right_expr.data_type
        )
        kind = ExpressionKind._validate_infer_kind([left_expr.kind, right_expr.kind])

        # Wrap operands in parentheses if needed based on precedence
        left = parens_if_needed(left_expr.expression, "||", operand_type="left")
        right = parens_if_needed(right_expr.expression, "||", operand_type="right")

        or_expr = exp.Or(this=left, expression=right)

        return TypedSelectExpression.from_sqlglot(or_expr, DataType.BOOLEAN, kind)


class BinaryAnd(BinaryLogicalBase):
    binary: Literal["&&"] = Field(
        default="&&",
        description="Binary AND operator, as in true && false = false",
        title="binary-and-op",
    )

    def compile(
        self,
        left_expr: TypedSelectExpression,
        right_expr: TypedSelectExpression,
        dialect: Dialect,
        timezone: str,
    ) -> TypedSelectExpression:
        self._validate_logical_operator_arg_types(
            left_expr.data_type, right_expr.data_type
        )
        kind = ExpressionKind._validate_infer_kind([left_expr.kind, right_expr.kind])

        # Wrap operands in parentheses if needed based on precedence
        left = parens_if_needed(left_expr.expression, "&&", operand_type="left")
        right = parens_if_needed(right_expr.expression, "&&", operand_type="right")

        and_expr = exp.And(this=left, expression=right)

        return TypedSelectExpression.from_sqlglot(and_expr, DataType.BOOLEAN, kind)
