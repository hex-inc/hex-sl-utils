from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import Field

from hex_sl.calc.ast.functions.base import DATETIME_TYPES, FuncBase
from hex_sl.expr import ExpressionContext

if TYPE_CHECKING:
    # This import seems to be needed to help mypy follow that the BinaryBase
    # lhs/rhs CalcExpr properties are available in child classes
    from hex_sl.calc.ast.args import Args  # noqa: F401
    from hex_sl.dialect.base import HexSLDialect
    from hex_sl.expr import TypedSelectExpression


class FuncDateDiffBase(FuncBase):
    fun: Literal[
        "diffweeks",
        "diffdays",
        "diffhours",
        "diffminutes",
        "diffseconds",
        "diffmilliseconds",
    ]

    def compile(
        self,
        arg_exprs: list[TypedSelectExpression],
        dialect: HexSLDialect,
        context: ExpressionContext,
        tz: str,
    ) -> TypedSelectExpression:
        ts0, ts1 = self._validate_n_args(arg_exprs, 2)
        self._validate_variadic_with_type(arg_exprs, DATETIME_TYPES, allow_empty=False)
        return dialect.date_diff(ts0, ts1, diff_fn=self.fun, timezone=tz)


class FuncDiffWeeks(FuncDateDiffBase):
    """Difference in weeks between two dates or timestamps"""

    fun: Literal["diffweeks"] = Field(
        default="diffweeks",
        description="Difference in weeks between two dates or timestamps",
        title="function-diff-weeks",
    )


class FuncDiffDays(FuncDateDiffBase):
    """Difference in days between two dates or timestamps"""

    fun: Literal["diffdays"] = Field(
        default="diffdays",
        description="Difference in days between two dates or timestamps",
        title="function-diff-days",
    )


class FuncDiffHours(FuncDateDiffBase):
    """Difference in hours between two dates or timestamps"""

    fun: Literal["diffhours"] = Field(
        default="diffhours",
        description="Difference in hours between two dates or timestamps",
        title="function-diff-hours",
    )


class FuncDiffMinutes(FuncDateDiffBase):
    """Difference in minutes between two dates or timestamps"""

    fun: Literal["diffminutes"] = Field(
        default="diffminutes",
        description="Difference in minutes between two dates or timestamps",
        title="function-diff-minutes",
    )


class FuncDiffSeconds(FuncDateDiffBase):
    """Difference in seconds between two dates or timestamps"""

    fun: Literal["diffseconds"] = Field(
        default="diffseconds",
        description="Difference in seconds between two dates or timestamps",
        title="function-diff-seconds",
    )


class FuncDiffMilliseconds(FuncDateDiffBase):
    """Difference in milliseconds between two dates or timestamps"""

    fun: Literal["diffmilliseconds"] = Field(
        default="diffmilliseconds",
        description="Difference in milliseconds between two dates or timestamps",
        title="function-diff-milliseconds",
    )
