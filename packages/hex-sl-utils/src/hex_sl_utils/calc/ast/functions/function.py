from typing import Annotated, Union

from hex_sl_utils.calc.ast.functions.aggs import (
    FuncAvg,
    FuncCount,
    FuncCountDistinct,
    FuncMax,
    FuncMedian,
    FuncMin,
    FuncPercentile,
    FuncPercentileApprox,
    FuncStddev,
    FuncStddevPop,
    FuncSum,
    FuncSumBoolean,
    FuncVariance,
    FuncVariancePop,
)
from hex_sl_utils.calc.ast.functions.cast import (
    FuncToBoolean,
    FuncToDate,
    FuncToDatetime,
    FuncToNumber,
    FuncToText,
)
from hex_sl_utils.calc.ast.functions.control import (
    FuncCoalesce,
    FuncIf,
    FuncIsFinite,
    FuncIsNull,
    FuncIsOneOf,
    FuncSwitch,
)
from hex_sl_utils.calc.ast.functions.date_diff import (
    FuncDiffDays,
    FuncDiffHours,
    FuncDiffMilliseconds,
    FuncDiffMinutes,
    FuncDiffSeconds,
    FuncDiffWeeks,
)
from hex_sl_utils.calc.ast.functions.date_part import (
    FuncDatetimeToEpochMs,
    FuncDay,
    FuncDayOfWeek,
    FuncEpochMsToDatetime,
    FuncHour,
    FuncMillisecond,
    FuncMinute,
    FuncMonth,
    FuncQuarter,
    FuncSecond,
    FuncYear,
)
from hex_sl_utils.calc.ast.functions.date_trunc import (
    FuncTruncDay,
    FuncTruncHour,
    FuncTruncMillisecond,
    FuncTruncMinute,
    FuncTruncMonth,
    FuncTruncQuarter,
    FuncTruncSecond,
    FuncTruncWeek,
    FuncTruncWeekMonday,
    FuncTruncYear,
)
from hex_sl_utils.calc.ast.functions.instant import FuncNow, FuncToday
from hex_sl_utils.calc.ast.functions.internal import (
    FuncChartToDatetime,
    FuncChartToNumber,
)
from hex_sl_utils.calc.ast.functions.rolling import (
    FuncCumulativeAvg,
    FuncCumulativeCount,
    FuncCumulativeCountDistinct,
    FuncCumulativeMax,
    FuncCumulativeMedian,
    FuncCumulativeMin,
    FuncCumulativeStddev,
    FuncCumulativeStddevPop,
    FuncCumulativeSum,
    FuncCumulativeSumBoolean,
    FuncCumulativeVariance,
    FuncCumulativeVariancePop,
)
from hex_sl_utils.calc.ast.functions.string import (
    FuncConcat,
    FuncContains,
    FuncEndsWith,
    FuncLeft,
    FuncLength,
    FuncLower,
    FuncRight,
    FuncSplitPart,
    FuncStartsWith,
    FuncSubstitute,
    FuncUpper,
)
from hex_sl_utils.calc.ast.functions.unary_math import (
    FuncAbs,
    FuncCeil,
    FuncCos,
    FuncCot,
    FuncExp,
    FuncFloor,
    FuncRound,
    FuncSin,
    FuncSqrt,
    FuncTan,
)
from hex_sl_utils.exception import UserFacingError

TaggedFuncExprUnion = Union[
    # String functions
    Annotated[FuncConcat, FuncConcat.tag()],
    Annotated[FuncLeft, FuncLeft.tag()],
    Annotated[FuncRight, FuncRight.tag()],
    Annotated[FuncSubstitute, FuncSubstitute.tag()],
    Annotated[FuncUpper, FuncUpper.tag()],
    Annotated[FuncLower, FuncLower.tag()],
    Annotated[FuncContains, FuncContains.tag()],
    Annotated[FuncStartsWith, FuncStartsWith.tag()],
    Annotated[FuncEndsWith, FuncEndsWith.tag()],
    Annotated[FuncLength, FuncLength.tag()],
    Annotated[FuncSplitPart, FuncSplitPart.tag()],
    # Math functions
    Annotated[FuncExp, FuncExp.tag()],
    Annotated[FuncCeil, FuncCeil.tag()],
    Annotated[FuncFloor, FuncFloor.tag()],
    Annotated[FuncRound, FuncRound.tag()],
    Annotated[FuncAbs, FuncAbs.tag()],
    Annotated[FuncSin, FuncSin.tag()],
    Annotated[FuncCos, FuncCos.tag()],
    Annotated[FuncSqrt, FuncSqrt.tag()],
    Annotated[FuncTan, FuncTan.tag()],
    Annotated[FuncCot, FuncCot.tag()],
    # Control functions
    Annotated[FuncCoalesce, FuncCoalesce.tag()],
    Annotated[FuncIf, FuncIf.tag()],
    Annotated[FuncIsFinite, FuncIsFinite.tag()],
    Annotated[FuncIsNull, FuncIsNull.tag()],
    Annotated[FuncIsOneOf, FuncIsOneOf.tag()],
    Annotated[FuncSwitch, FuncSwitch.tag()],
    # Aggregate functions
    Annotated[FuncMin, FuncMin.tag()],
    Annotated[FuncMax, FuncMax.tag()],
    Annotated[FuncAvg, FuncAvg.tag()],
    Annotated[FuncCount, FuncCount.tag()],
    Annotated[FuncCountDistinct, FuncCountDistinct.tag()],
    Annotated[FuncSum, FuncSum.tag()],
    Annotated[FuncSumBoolean, FuncSumBoolean.tag()],
    Annotated[FuncPercentile, FuncPercentile.tag()],
    Annotated[FuncPercentileApprox, FuncPercentileApprox.tag()],
    Annotated[FuncStddev, FuncStddev.tag()],
    Annotated[FuncStddevPop, FuncStddevPop.tag()],
    Annotated[FuncVariance, FuncVariance.tag()],
    Annotated[FuncVariancePop, FuncVariancePop.tag()],
    Annotated[FuncMedian, FuncMedian.tag()],
    # Cumulative functions
    Annotated[FuncCumulativeSum, FuncCumulativeSum.tag()],
    Annotated[FuncCumulativeSumBoolean, FuncCumulativeSumBoolean.tag()],
    Annotated[FuncCumulativeAvg, FuncCumulativeAvg.tag()],
    Annotated[FuncCumulativeCount, FuncCumulativeCount.tag()],
    Annotated[FuncCumulativeCountDistinct, FuncCumulativeCountDistinct.tag()],
    Annotated[FuncCumulativeMin, FuncCumulativeMin.tag()],
    Annotated[FuncCumulativeMax, FuncCumulativeMax.tag()],
    Annotated[FuncCumulativeMedian, FuncCumulativeMedian.tag()],
    Annotated[FuncCumulativeStddev, FuncCumulativeStddev.tag()],
    Annotated[FuncCumulativeStddevPop, FuncCumulativeStddevPop.tag()],
    Annotated[FuncCumulativeVariance, FuncCumulativeVariance.tag()],
    Annotated[FuncCumulativeVariancePop, FuncCumulativeVariancePop.tag()],
    # Cast functions
    Annotated[FuncToDatetime, FuncToDatetime.tag()],
    Annotated[FuncToDate, FuncToDate.tag()],
    Annotated[FuncToNumber, FuncToNumber.tag()],
    Annotated[FuncToText, FuncToText.tag()],
    Annotated[FuncToBoolean, FuncToBoolean.tag()],
    # Date part functions
    Annotated[FuncYear, FuncYear.tag()],
    Annotated[FuncQuarter, FuncQuarter.tag()],
    Annotated[FuncMonth, FuncMonth.tag()],
    Annotated[FuncDay, FuncDay.tag()],
    Annotated[FuncDayOfWeek, FuncDayOfWeek.tag()],
    Annotated[FuncHour, FuncHour.tag()],
    Annotated[FuncMinute, FuncMinute.tag()],
    Annotated[FuncSecond, FuncSecond.tag()],
    Annotated[FuncMillisecond, FuncMillisecond.tag()],
    Annotated[FuncEpochMsToDatetime, FuncEpochMsToDatetime.tag()],
    Annotated[FuncDatetimeToEpochMs, FuncDatetimeToEpochMs.tag()],
    # Date trunc functions
    Annotated[FuncTruncYear, FuncTruncYear.tag()],
    Annotated[FuncTruncQuarter, FuncTruncQuarter.tag()],
    Annotated[FuncTruncMonth, FuncTruncMonth.tag()],
    Annotated[FuncTruncWeek, FuncTruncWeek.tag()],
    Annotated[FuncTruncWeekMonday, FuncTruncWeekMonday.tag()],
    Annotated[FuncTruncDay, FuncTruncDay.tag()],
    Annotated[FuncTruncHour, FuncTruncHour.tag()],
    Annotated[FuncTruncMinute, FuncTruncMinute.tag()],
    Annotated[FuncTruncSecond, FuncTruncSecond.tag()],
    Annotated[FuncTruncMillisecond, FuncTruncMillisecond.tag()],
    # Date diff functions
    Annotated[FuncDiffWeeks, FuncDiffWeeks.tag()],
    Annotated[FuncDiffDays, FuncDiffDays.tag()],
    Annotated[FuncDiffHours, FuncDiffHours.tag()],
    Annotated[FuncDiffMinutes, FuncDiffMinutes.tag()],
    Annotated[FuncDiffSeconds, FuncDiffSeconds.tag()],
    Annotated[FuncDiffMilliseconds, FuncDiffMilliseconds.tag()],
    # Instant functions
    Annotated[FuncNow, FuncNow.tag()],
    Annotated[FuncToday, FuncToday.tag()],
    # Internal functions
    Annotated[FuncChartToNumber, FuncChartToNumber.tag()],
    Annotated[FuncChartToDatetime, FuncChartToDatetime.tag()],
]


def func_for_name(name: str) -> type[TaggedFuncExprUnion]:
    name_lower = name.lower()
    if name_lower == "concat":
        return FuncConcat
    elif name_lower == "left":
        return FuncLeft
    elif name_lower == "right":
        return FuncRight
    elif name_lower == "substitute":
        return FuncSubstitute
    elif name_lower == "upper":
        return FuncUpper
    elif name_lower == "lower":
        return FuncLower
    elif name_lower == "contains":
        return FuncContains
    elif name_lower == "startswith":
        return FuncStartsWith
    elif name_lower == "endswith":
        return FuncEndsWith
    elif name_lower == "splitpart":
        return FuncSplitPart
    elif name_lower == "length":
        return FuncLength
    elif name_lower == "abs":
        return FuncAbs
    elif name_lower == "round":
        return FuncRound
    elif name_lower == "ceil":
        return FuncCeil
    elif name_lower == "floor":
        return FuncFloor
    elif name_lower == "exp":
        return FuncExp
    elif name_lower == "cos":
        return FuncCos
    elif name_lower == "cot":
        return FuncCot
    elif name_lower == "sin":
        return FuncSin
    elif name_lower == "sqrt":
        return FuncSqrt
    elif name_lower == "tan":
        return FuncTan
    elif name_lower == "if":
        return FuncIf
    elif name_lower == "switch":
        return FuncSwitch
    elif name_lower == "isnull":
        return FuncIsNull
    elif name_lower == "coalesce":
        return FuncCoalesce
    elif name_lower == "isfinite":
        return FuncIsFinite
    elif name_lower == "isoneof":
        return FuncIsOneOf
    elif name_lower == "min":
        return FuncMin
    elif name_lower == "max":
        return FuncMax
    elif name_lower in ("mean", "avg", "average"):
        return FuncAvg
    elif name_lower == "count":
        return FuncCount
    elif name_lower == "countdistinct":
        return FuncCountDistinct
    elif name_lower == "sum":
        return FuncSum
    elif name_lower == "sumboolean":
        return FuncSumBoolean
    elif name_lower == "percentile":
        return FuncPercentile
    elif name_lower == "percentileapprox":
        return FuncPercentileApprox
    elif name_lower == "stddev":
        return FuncStddev
    elif name_lower == "stddevpop":
        return FuncStddevPop
    elif name_lower == "variance":
        return FuncVariance
    elif name_lower == "variancepop":
        return FuncVariancePop
    elif name_lower == "median":
        return FuncMedian
    # Cumulatives
    elif name_lower == "cumulativesum":
        return FuncCumulativeSum
    elif name_lower == "cumulativemin":
        return FuncCumulativeMin
    elif name_lower == "cumulativemax":
        return FuncCumulativeMax
    elif name_lower == "cumulativeavg":
        return FuncCumulativeAvg
    elif name_lower == "cumulativemedian":
        return FuncCumulativeMedian
    elif name_lower == "cumulativestddev":
        return FuncCumulativeStddev
    elif name_lower == "cumulativestddevpop":
        return FuncCumulativeStddevPop
    elif name_lower == "cumulativevariance":
        return FuncCumulativeVariance
    elif name_lower == "cumulativevariancepop":
        return FuncCumulativeVariancePop
    elif name_lower == "cumulativecount":
        return FuncCumulativeCount
    elif name_lower == "cumulativecountdistinct":
        return FuncCumulativeCountDistinct
    elif name_lower == "cumulativesumboolean":
        return FuncCumulativeSumBoolean
    elif name_lower == "todatetime":
        return FuncToDatetime
    elif name_lower == "todate":
        return FuncToDate
    elif name_lower == "tonumber":
        return FuncToNumber
    elif name_lower == "totext":
        return FuncToText
    elif name_lower == "toboolean":
        return FuncToBoolean
    elif name_lower == "year":
        return FuncYear
    elif name_lower == "quarter":
        return FuncQuarter
    elif name_lower == "month":
        return FuncMonth
    elif name_lower == "dayofweek":
        return FuncDayOfWeek
    elif name_lower == "day":
        return FuncDay
    elif name_lower == "hour":
        return FuncHour
    elif name_lower == "minute":
        return FuncMinute
    elif name_lower == "second":
        return FuncSecond
    elif name_lower == "millisecond":
        return FuncMillisecond
    elif name_lower == "epochmstodatetime":
        return FuncEpochMsToDatetime
    elif name_lower == "datetimetoepochms":
        return FuncDatetimeToEpochMs
    elif name_lower == "truncyear":
        return FuncTruncYear
    elif name_lower == "truncquarter":
        return FuncTruncQuarter
    elif name_lower == "truncmonth":
        return FuncTruncMonth
    elif name_lower == "truncweek":
        return FuncTruncWeek
    elif name_lower == "truncweekmonday":
        return FuncTruncWeekMonday
    elif name_lower == "truncday":
        return FuncTruncDay
    elif name_lower == "trunchour":
        return FuncTruncHour
    elif name_lower == "truncminute":
        return FuncTruncMinute
    elif name_lower == "truncsecond":
        return FuncTruncSecond
    elif name_lower == "truncmillisecond":
        return FuncTruncMillisecond
    elif name_lower == "diffweeks":
        return FuncDiffWeeks
    elif name_lower == "diffdays":
        return FuncDiffDays
    elif name_lower == "diffhours":
        return FuncDiffHours
    elif name_lower == "diffminutes":
        return FuncDiffMinutes
    elif name_lower == "diffseconds":
        return FuncDiffSeconds
    elif name_lower == "diffmilliseconds":
        return FuncDiffMilliseconds
    elif name_lower == "now":
        return FuncNow
    elif name_lower == "today":
        return FuncToday
    elif name_lower == "_chart_tonumber":
        return FuncChartToNumber
    elif name_lower == "_chart_todatetime":
        return FuncChartToDatetime
    else:
        msg = f"Unknown function: {name}"
        raise UserFacingError(msg)
