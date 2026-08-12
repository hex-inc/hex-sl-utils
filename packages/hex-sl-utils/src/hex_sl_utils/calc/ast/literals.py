from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING, Annotated, Optional, TypeVar, Union

from pydantic import Field, Tag

from hex_sl.calc.ast.base import ExprBase
from hex_sl.calc.visitor import CalcVisitor
from hex_sl.dialect.base import HexSLDialect
from hex_sl.expr import TypedSelectExpression

if TYPE_CHECKING:
    pass

T = TypeVar("T")


class LiteralNumber(ExprBase):
    number_value: Union[int, float] = Field(
        description="Number literal, as in 22 or 10.5", alias="number"
    )

    @classmethod
    def tag(cls) -> Tag:
        return Tag("number")

    def accept(self, visitor: CalcVisitor[T]) -> T:
        return visitor.visit_literal_number(self)

    def compile(self, dialect: HexSLDialect) -> TypedSelectExpression:
        return dialect.compile_literal(self.number_value)


class LiteralString(ExprBase):
    str_value: str = Field(description="String literal, as in 'hello'", alias="str")

    @classmethod
    def tag(cls) -> Tag:
        return Tag("str")

    def accept(self, visitor: CalcVisitor[T]) -> T:
        return visitor.visit_literal_string(self)

    def compile(self, dialect: HexSLDialect) -> TypedSelectExpression:
        return dialect.compile_literal(self.str_value)


class LiteralBool(ExprBase):
    bool_value: bool = Field(
        description="Boolean literal, as in true or false", alias="bool"
    )

    @classmethod
    def tag(cls) -> Tag:
        return Tag("bool")

    def accept(self, visitor: CalcVisitor[T]) -> T:
        return visitor.visit_literal_bool(self)

    def compile(self, dialect: HexSLDialect) -> TypedSelectExpression:
        return dialect.compile_literal(self.bool_value)


class LiteralTimestamp(ExprBase):
    timestamp_value: datetime = Field(
        description="Timestamp literal, as in 2023-06-01T12:34:56", alias="timestamp"
    )

    @classmethod
    def tag(cls) -> Tag:
        return Tag("timestamp")

    def accept(self, visitor: CalcVisitor[T]) -> T:
        return visitor.visit_literal_timestamp(self)

    def compile(self, dialect: HexSLDialect) -> TypedSelectExpression:
        return dialect.compile_literal(self.timestamp_value)


class LiteralDate(ExprBase):
    date_value: date = Field(description="Date literal, as in 2023-06-01", alias="date")

    @classmethod
    def tag(cls) -> Tag:
        return Tag("date")

    def accept(self, visitor: CalcVisitor[T]) -> T:
        return visitor.visit_literal_date(self)

    def compile(self, dialect: HexSLDialect) -> TypedSelectExpression:
        return dialect.compile_literal(self.date_value)


class LiteralNull(ExprBase):
    null_value: None = Field(default=None, description="Null literal", alias="null")
    position: Optional[int] = Field(
        default=None, description="Position of the null literal in calc expression"
    )

    @classmethod
    def tag(cls) -> Tag:
        return Tag("null")

    def accept(self, visitor: CalcVisitor[T]) -> T:
        return visitor.visit_literal_null(self)

    def compile(self, dialect: HexSLDialect) -> TypedSelectExpression:
        return dialect.compile_literal(None)


TaggedLiteralExprUnion = Union[
    Annotated[LiteralNumber, LiteralNumber.tag()],
    Annotated[LiteralString, LiteralString.tag()],
    Annotated[LiteralBool, LiteralBool.tag()],
    Annotated[LiteralTimestamp, LiteralTimestamp.tag()],
    Annotated[LiteralDate, LiteralDate.tag()],
    Annotated[LiteralNull, LiteralNull.tag()],
]
