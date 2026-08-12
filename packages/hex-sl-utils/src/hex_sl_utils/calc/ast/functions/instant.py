# pyright: reportCallIssue=false, reportIncompatibleVariableOverride=false
from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import Field

from hex_sl_utils.calc.ast.functions.base import FuncBase
from hex_sl_utils.calc.compiled import ExpressionContext

if TYPE_CHECKING:
    # This import seems to be needed to help mypy follow that the BinaryBase
    # lhs/rhs CalcExpr properties are available in child classes
    from hex_sl_utils.calc.ast.args import Args  # noqa: F401
    from hex_sl_utils.calc.compiled import TypedSelectExpression
    from hex_sl_utils.calc.protocols import CalcDialect


class FuncToday(FuncBase):
    fun: Literal["today"] = Field(
        default="today",
        description="Today's date",
        title="function-today",
    )

    def compile(
        self,
        arg_exprs: list[TypedSelectExpression],
        dialect: CalcDialect,
        context: ExpressionContext,
        tz: str,
    ) -> TypedSelectExpression:
        self._validate_no_args(arg_exprs)
        return dialect.today(timezone=tz)


class FuncNow(FuncBase):
    fun: Literal["now"] = Field(
        default="now",
        description="Current timestamp",
        title="function-now",
    )

    def compile(
        self,
        arg_exprs: list[TypedSelectExpression],
        dialect: CalcDialect,
        context: ExpressionContext,
        tz: str,
    ) -> TypedSelectExpression:
        self._validate_no_args(arg_exprs)
        return dialect.now(timezone=tz)
