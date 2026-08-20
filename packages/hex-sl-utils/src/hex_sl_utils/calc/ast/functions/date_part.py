# pyright: reportIncompatibleVariableOverride=false

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import Field

from hex_sl_utils.calc.ast.functions.base import DATETIME_TYPES, FuncBase
from hex_sl_utils.datatype import DataType
from hex_sl_utils.expr import ExpressionContext

if TYPE_CHECKING:
    from hex_sl_utils.dialect.dialect import Dialect
    from hex_sl_utils.expr import TypedSelectExpression


class FuncDatePartBase(FuncBase):
    fun: Literal["year", "quarter", "month", "day", "dayofweek"]

    def compile(
        self,
        arg_exprs: list[TypedSelectExpression],
        dialect: Dialect,
        context: ExpressionContext,
        tz: str,
    ) -> TypedSelectExpression:
        arg = self._validate_single_arg(arg_exprs, DATETIME_TYPES)
        if self.fun == "dayofweek":
            return dialect.day_of_week_part(arg, timezone=tz)
        else:
            return dialect.date_part(arg, unit=self.fun, timezone=tz)


class FuncYear(FuncDatePartBase):
    """Years part of a date"""

    fun: Literal["year"] = Field(
        default="year",
        description="Years part of a date or timestamp",
        title="function-year",
    )


class FuncQuarter(FuncDatePartBase):
    """Quarters part of a date (1-4)"""

    fun: Literal["quarter"] = Field(
        default="quarter",
        description="Quarters part of a date or timestamp",
        title="function-quarter",
    )


class FuncMonth(FuncDatePartBase):
    """Months part of a date (1-12)"""

    fun: Literal["month"] = Field(
        default="month",
        description="Months part of a date or timestamp",
        title="function-month",
    )


class FuncDay(FuncDatePartBase):
    """Day-of-month part of a date (1-31)"""

    fun: Literal["day"] = Field(
        default="day",
        description="Days part of a date or timestamp",
        title="function-day",
    )


class FuncDayOfWeek(FuncDatePartBase):
    """Day-of-week part of a date (Sun(1)-Sat(7))"""

    fun: Literal["dayofweek"] = Field(
        default="dayofweek",
        description="Day-of-week part of a date or timestamp",
        title="function-dayofweek",
    )


class FuncTimePartBase(FuncBase):
    fun: Literal["hour", "minute", "second", "millisecond"]

    def compile(
        self,
        arg_exprs: list[TypedSelectExpression],
        dialect: Dialect,
        context: ExpressionContext,
        tz: str,
    ) -> TypedSelectExpression:
        arg = self._validate_single_arg(arg_exprs, DATETIME_TYPES)
        return dialect.time_part(arg, unit=self.fun, timezone=tz)


class FuncHour(FuncTimePartBase):
    """Hours part of a timestamp (0-23)"""

    fun: Literal["hour"] = Field(
        default="hour",
        description="Hours part of a timestamp",
        title="function-hour",
    )


class FuncMinute(FuncTimePartBase):
    """Minutes part of a timestamp (0-59)"""

    fun: Literal["minute"] = Field(
        default="minute",
        description="Minutes part of a timestamp",
        title="function-minute",
    )


class FuncSecond(FuncTimePartBase):
    """Seconds part of a timestamp (0-59)"""

    fun: Literal["second"] = Field(
        default="second",
        description="Seconds part of a timestamp",
        title="function-second",
    )


class FuncMillisecond(FuncTimePartBase):
    """Milliseconds part of a timestamp (0-999)"""

    fun: Literal["millisecond"] = Field(
        default="millisecond",
        description="Milliseconds part of a timestamp",
        title="function-millisecond",
    )


class FuncDatetimeToEpochMs(FuncBase):
    fun: Literal["datetimetoepochms"] = Field(
        default="datetimetoepochms",
        description=(
            "Converts a timestamp to the number of milliseconds since the unix epoch"
        ),
        title="function-datetimetoepochms",
    )

    def compile(
        self,
        arg_exprs: list[TypedSelectExpression],
        dialect: Dialect,
        context: ExpressionContext,
        tz: str,
    ) -> TypedSelectExpression:
        arg = self._validate_single_arg(arg_exprs, DATETIME_TYPES)
        return dialect.datetime_to_epoch_ms(arg)


class FuncEpochMsToDatetime(FuncBase):
    fun: Literal["epochmstodatetime"] = Field(
        default="epochmstodatetime",
        description=(
            "Converts a number of milliseconds since the unix epoch to a timestamp"
        ),
        title="function-epochmstodatetime",
    )

    def compile(
        self,
        arg_exprs: list[TypedSelectExpression],
        dialect: Dialect,
        context: ExpressionContext,
        tz: str,
    ) -> TypedSelectExpression:
        arg = self._validate_single_arg(arg_exprs, DataType.NUMBER)
        return dialect.epoch_ms_to_timestamp(arg)
