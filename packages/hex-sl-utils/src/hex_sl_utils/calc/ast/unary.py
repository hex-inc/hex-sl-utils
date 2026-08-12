from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Literal, TypeVar, Union

from pydantic import Field, Tag

from hex_sl._vendor.sqlglot import exp
from hex_sl.calc.ast.base import ExprBase
from hex_sl.calc.operators import UnaryOp
from hex_sl.calc.parentheses import parens_if_needed
from hex_sl.datatype import DataType
from hex_sl.dialect.base import HexSLDialect
from hex_sl.expr import TypedSelectExpression
from hex_sl.utils import TypeCheckError, UserFacingError

if TYPE_CHECKING:
    from hex_sl.calc.ast import CalcExpr
    from hex_sl.calc.visitor import CalcVisitor

T = TypeVar("T")


class UnaryBase(ExprBase):
    arg: CalcExpr
    unary: UnaryOp

    @classmethod
    def tag(cls) -> Tag:
        unary = cls.model_fields["unary"].default
        return Tag(f"unary:{unary}")

    def get_op(self) -> UnaryOp:
        return self.unary

    def accept(self, visitor: CalcVisitor[T]) -> T:
        return visitor.visit_unary(self)

    def compile(
        self, arg_expr: TypedSelectExpression, dialect: HexSLDialect
    ) -> TypedSelectExpression:
        """
        Compiles the unary operation into a TypedSelectExpression.
        Each subclass should override this method to provide the correct
        SQL function expression, data type, and kind.
        """
        msg = "Each unary operation must implement its own compile method."
        raise NotImplementedError(msg)


class UnaryMinus(UnaryBase):
    unary: Literal["-"] = Field(
        default="-",
        description="Unary minus operator, as in -23",
        title="unary-minus-op",
    )

    def compile(
        self, arg_expr: TypedSelectExpression, dialect: HexSLDialect
    ) -> TypedSelectExpression:
        if arg_expr.data_type != DataType.NUMBER:
            msg = "Unary minus operation requires a numeric argument."
            raise TypeCheckError(msg)

        # Wrap the operand in parentheses if needed
        wrapped_expr = parens_if_needed(
            arg_expr.expression, self.unary, operand_type="unary"
        )
        neg_expr = exp.Neg(this=wrapped_expr)
        return TypedSelectExpression.from_sqlglot(
            neg_expr, DataType.NUMBER, arg_expr.kind
        )


class UnaryPlus(UnaryBase):
    unary: Literal["+"] = Field(
        default="+",
        description="Unary plus operator, as in +23",
        title="unary-plus-op",
    )

    def compile(
        self, arg_expr: TypedSelectExpression, dialect: HexSLDialect
    ) -> TypedSelectExpression:
        if arg_expr.data_type != DataType.NUMBER:
            msg = "Unary plus operation requires a numeric argument."
            raise TypeCheckError(msg)

        return arg_expr


class UnaryNot(UnaryBase):
    unary: Literal["!"] = Field(
        default="!",
        description="Unary NOT operator, as in !true = false",
        title="unary-not-op",
    )

    def compile(
        self, arg_expr: TypedSelectExpression, dialect: HexSLDialect
    ) -> TypedSelectExpression:
        if arg_expr.data_type != DataType.BOOLEAN:
            msg = "Unary NOT operation requires a boolean argument."
            raise TypeCheckError(msg)

        # Wrap the operand in parentheses if needed
        wrapped_expr = parens_if_needed(
            arg_expr.expression, self.unary, operand_type="unary"
        )
        not_expr = exp.Not(this=wrapped_expr)
        return TypedSelectExpression.from_sqlglot(
            not_expr, DataType.BOOLEAN, arg_expr.kind
        )


TaggedUnaryExprUnion = Union[
    Annotated[UnaryMinus, UnaryMinus.tag()],
    Annotated[UnaryPlus, UnaryPlus.tag()],
    Annotated[UnaryNot, UnaryNot.tag()],
]


def unary_for_name(name: str) -> type[TaggedUnaryExprUnion]:
    name_lower = name.lower()
    if name_lower == "-":
        return UnaryMinus
    elif name_lower == "+":
        return UnaryPlus
    elif name_lower in ("!", "not"):
        return UnaryNot
    else:
        msg = f"Unknown unary operator: {name}"
        raise UserFacingError(msg)
