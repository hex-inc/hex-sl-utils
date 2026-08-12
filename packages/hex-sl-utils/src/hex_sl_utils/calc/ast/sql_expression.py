# pyright: reportCallIssue=false, reportIncompatibleVariableOverride=false
from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, TypeVar

from pydantic import Field, Tag

from hex_sl_utils.calc.ast.base import ExprBase
from hex_sl_utils.types import DataType

if TYPE_CHECKING:
    from hex_sl_utils.calc.visitor import CalcVisitor

T = TypeVar("T")


class SqlExpression(ExprBase):
    """SQL expression node for manual SQL injection into Calc AST.

    This node allows embedding raw SQL expressions into the Calc expression system.
    Column references in the SQL can be substituted using the _hexsl_calc()
    placeholder mechanism, which defers compilation until full context is available.
    """

    sql: str = Field(description="SQL expression string")
    data_type: DataType = Field(description="Result data type")

    @classmethod
    def tag(cls) -> Tag:
        return Tag("sql_expr")

    def accept(self, visitor: CalcVisitor[T]) -> T:
        return visitor.visit_sql_expression(self)


# Tagged version for discriminated union
TaggedSqlExpression = Annotated[SqlExpression, Tag("sql_expr")]
