# pyright: reportCallIssue=false, reportIncompatibleVariableOverride=false
from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from pydantic import Tag

from hex_sl_utils.calc.ast.base import ExprBase
from hex_sl_utils.calc.compiled import TypedSelectExpression
from hex_sl_utils.calc.operators import BinaryOp
from hex_sl_utils.calc.protocols import CalcDialect
from hex_sl_utils.calc.visitor import CalcVisitor

if TYPE_CHECKING:
    from hex_sl_utils.calc.ast import CalcExpr

T = TypeVar("T")


class BinaryBase(ExprBase):
    lhs: CalcExpr
    rhs: CalcExpr
    binary: BinaryOp

    @classmethod
    def tag(cls) -> Tag:
        binary = cls.model_fields["binary"].default
        return Tag(f"binary:{binary}")

    def get_op(self) -> str:
        return self.binary

    def accept(self, visitor: CalcVisitor[T]) -> T:
        return visitor.visit_binary(self)

    def compile(
        self,
        left_expr: TypedSelectExpression,
        right_expr: TypedSelectExpression,
        dialect: CalcDialect,
        timezone: str,
    ) -> TypedSelectExpression:
        """
        Compiles the binary operation into a TypedSelectExpression.

        Args:
            left_expr: The left hand side of the binary operation.
            right_expr: The right hand side of the binary operation.
            dialect: The dialect to compile the binary operation for.
            timezone: The timezone to use for the binary operation.

        Returns:
            TypedSelectExpression: The compiled binary operation.

        Raises:
            NotImplementedError: If binary operation has not implemented compilation
            TypeCheckError: If arguments have invalid data types or kinds for operator
        """
        msg = "Subclass must implement compile method"
        raise NotImplementedError(msg)


__all__ = [
    "BinaryBase",
]
