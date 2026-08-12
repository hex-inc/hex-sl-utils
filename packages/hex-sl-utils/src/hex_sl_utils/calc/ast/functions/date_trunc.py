# pyright: reportCallIssue=false, reportIncompatibleVariableOverride=false
from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import Field

from hex_sl_utils.calc.ast.functions.base import DATETIME_TYPES, FuncBase
from hex_sl_utils.calc.compiled import ExpressionContext
from hex_sl_utils.calc.protocols import TruncUnit

if TYPE_CHECKING:
    # This import seems to be needed to help mypy follow that the BinaryBase
    # lhs/rhs CalcExpr properties are available in child classes
    from hex_sl_utils.calc.ast.args import Args  # noqa: F401
    from hex_sl_utils.calc.compiled import TypedSelectExpression
    from hex_sl_utils.calc.protocols import CalcDialect


class FuncTruncBase(FuncBase):
    fun: Literal[
        "truncyear",
        "truncquarter",
        "truncmonth",
        "truncweek",
        "truncweekmonday",
        "truncday",
        "trunchour",
        "truncminute",
        "truncsecond",
        "truncmillisecond",
    ]

    def compile(
        self,
        arg_exprs: list[TypedSelectExpression],
        dialect: CalcDialect,
        context: ExpressionContext,
        tz: str,
    ) -> TypedSelectExpression:
        """
        Truncate datetime down to the nearest unit

        Accepts values of type Date, Timestamp, TimestampTZ, and Date,
        and always returns a value of the same type.
        """
        from hex_sl_utils.types import DataType

        arg = self._validate_single_arg(arg_exprs, DATETIME_TYPES)
        if arg.data_type == DataType.DATE and self.fun in (
            "trunchour",
            "truncminute",
            "truncsecond",
            "truncmillisecond",
        ):
            # Return date as-is if truncating to lower precision
            return arg
        else:
            fun_to_truncunit: dict[str, TruncUnit] = {
                "truncyear": "year",
                "truncquarter": "quarter",
                "truncmonth": "month",
                "truncweek": "week",
                "truncweekmonday": "weekmonday",
                "truncday": "day",
                "trunchour": "hour",
                "truncminute": "minute",
                "truncsecond": "second",
                "truncmillisecond": "millisecond",
            }
            return dialect.datetime_trunc(arg, fun_to_truncunit[self.fun], tz)


class FuncTruncYear(FuncTruncBase):
    """Truncate datetime down to the nearest year"""

    fun: Literal["truncyear"] = Field(
        default="truncyear",
        description="Truncate datetime down to the nearest year",
        title="function-trunc-year",
    )


class FuncTruncQuarter(FuncTruncBase):
    """Truncate datetime down to the nearest quarter"""

    fun: Literal["truncquarter"] = Field(
        default="truncquarter",
        description="Truncate datetime down to the nearest quarter",
        title="function-trunc-quarter",
    )


class FuncTruncMonth(FuncTruncBase):
    """Truncate datetime down to the nearest month"""

    fun: Literal["truncmonth"] = Field(
        default="truncmonth",
        description="Truncate datetime down to the nearest month",
        title="function-trunc-month",
    )


class FuncTruncWeek(FuncTruncBase):
    """Truncate datetime down to the nearest week starting on Sunday"""

    fun: Literal["truncweek"] = Field(
        default="truncweek",
        description=(
            "Truncate datetime down to the nearest week (weeks start on Sunday)"
        ),
        title="function-trunc-week",
    )


class FuncTruncWeekMonday(FuncTruncBase):
    """Truncate datetime down to the nearest week starting on Monday"""

    fun: Literal["truncweekmonday"] = Field(
        default="truncweekmonday",
        description=(
            "Truncate datetime down to the nearest week (weeks start on Monday)"
        ),
        title="function-trunc-weekmonday",
    )


class FuncTruncDay(FuncTruncBase):
    """Truncate datetime down to the nearest day"""

    fun: Literal["truncday"] = Field(
        default="truncday",
        description="Truncate datetime down to the nearest day",
        title="function-trunc-day",
    )


class FuncTruncHour(FuncTruncBase):
    """Truncate datetime down to the nearest hour"""

    fun: Literal["trunchour"] = Field(
        default="trunchour",
        description="Truncate datetime down to the nearest hour",
        title="function-trunc-hour",
    )


class FuncTruncMinute(FuncTruncBase):
    """Truncate datetime down to the nearest minute"""

    fun: Literal["truncminute"] = Field(
        default="truncminute",
        description="Truncate datetime down to the nearest minute",
        title="function-trunc-minute",
    )


class FuncTruncSecond(FuncTruncBase):
    """Truncate datetime down to the nearest second"""

    fun: Literal["truncsecond"] = Field(
        default="truncsecond",
        description="Truncate datetime down to the nearest second",
        title="function-trunc-second",
    )


class FuncTruncMillisecond(FuncTruncBase):
    """Truncate datetime down to the nearest millisecond"""

    fun: Literal["truncmillisecond"] = Field(
        default="truncmillisecond",
        description="Truncate datetime down to the nearest millisecond",
        title="function-trunc-millisecond",
    )
