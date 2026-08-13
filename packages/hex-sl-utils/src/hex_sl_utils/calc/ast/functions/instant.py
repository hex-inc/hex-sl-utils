# pyright: reportIncompatibleVariableOverride=false

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import Field

from hex_sl_utils.calc.ast.functions.base import FuncBase
from hex_sl_utils.expr import ExpressionContext

if TYPE_CHECKING:
    from hex_sl_utils.dialect.dialect import Dialect
    from hex_sl_utils.expr import TypedSelectExpression


class FuncToday(FuncBase):
    fun: Literal["today"] = Field(
        default="today",
        description="Today's date",
        title="function-today",
    )

    def compile(
        self,
        arg_exprs: list[TypedSelectExpression],
        dialect: Dialect,
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
        dialect: Dialect,
        context: ExpressionContext,
        tz: str,
    ) -> TypedSelectExpression:
        self._validate_no_args(arg_exprs)
        return dialect.now(timezone=tz)
