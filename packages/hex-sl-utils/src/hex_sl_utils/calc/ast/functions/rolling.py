# pyright: reportIncompatibleVariableOverride=false

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import Field

from hex_sl_utils.calc.ast.functions.aggs import (
    FuncAggBase,
    FuncAvg,
    FuncCount,
    FuncCountDistinct,
    FuncMax,
    FuncMedian,
    FuncMin,
    FuncStddev,
    FuncStddevPop,
    FuncSum,
    FuncSumBoolean,
    FuncVariance,
    FuncVariancePop,
)
from hex_sl_utils.expr import ExpressionContext, TypedSelectExpression

if TYPE_CHECKING:
    from hex_sl_utils.calc.ast.args import Args  # noqa: F401
    from hex_sl_utils.dialect.dialect import Dialect


class FuncRollingBase(FuncAggBase):
    def is_rolling(self) -> bool:
        return True

    def compile(
        self,
        arg_exprs: list[TypedSelectExpression],
        dialect: Dialect,
        context: ExpressionContext,
        tz: str,
    ) -> TypedSelectExpression:
        return self.build_agg().compile(arg_exprs, dialect, context, tz)

    def build_agg(self) -> FuncAggBase:
        msg = "Subclasses must implement this method"
        raise NotImplementedError(msg)


class FuncCumulativeBase(FuncRollingBase):
    pass


class FuncCumulativeSum(FuncCumulativeBase):
    fun: Literal["cumulativesum"] = Field(
        default="cumulativesum",
        description="Cumulative sum aggregation function",
        title="function-cumulativesum",
    )

    def build_agg(self) -> FuncAggBase:
        return FuncSum(args=self.args)


class FuncCumulativeMin(FuncCumulativeBase):
    fun: Literal["cumulativemin"] = Field(
        default="cumulativemin",
        description="Cumulative min aggregation function",
        title="function-cumulativemin",
    )

    def build_agg(self) -> FuncAggBase:
        return FuncMin(args=self.args)


class FuncCumulativeMax(FuncCumulativeBase):
    fun: Literal["cumulativemax"] = Field(
        default="cumulativemax",
        description="Cumulative max aggregation function",
        title="function-cumulativemax",
    )

    def build_agg(self) -> FuncAggBase:
        return FuncMax(args=self.args)


class FuncCumulativeAvg(FuncCumulativeBase):
    fun: Literal["cumulativeavg"] = Field(
        default="cumulativeavg",
        description="Cumulative avg aggregation function",
        title="function-cumulativeavg",
    )

    def build_agg(self) -> FuncAggBase:
        return FuncAvg(args=self.args)


class FuncCumulativeMedian(FuncCumulativeBase):
    fun: Literal["cumulativemedian"] = Field(
        default="cumulativemedian",
        description="Cumulative median aggregation function",
        title="function-cumulativemedian",
    )

    def build_agg(self) -> FuncAggBase:
        return FuncMedian(args=self.args)


class FuncCumulativeStddev(FuncCumulativeBase):
    fun: Literal["cumulativestddev"] = Field(
        default="cumulativestddev",
        description="Cumulative stddev aggregation function",
        title="function-cumulativestddev",
    )

    def build_agg(self) -> FuncAggBase:
        return FuncStddev(args=self.args)


class FuncCumulativeStddevPop(FuncCumulativeBase):
    fun: Literal["cumulativestddevpop"] = Field(
        default="cumulativestddevpop",
        description="Cumulative stddevpop aggregation function",
        title="function-cumulativestddevpop",
    )

    def build_agg(self) -> FuncAggBase:
        return FuncStddevPop(args=self.args)


class FuncCumulativeVariance(FuncCumulativeBase):
    fun: Literal["cumulativevariance"] = Field(
        default="cumulativevariance",
        description="Cumulative variance aggregation function",
        title="function-cumulativevariance",
    )

    def build_agg(self) -> FuncAggBase:
        return FuncVariance(args=self.args)


class FuncCumulativeVariancePop(FuncCumulativeBase):
    fun: Literal["cumulativevariancepop"] = Field(
        default="cumulativevariancepop",
        description="Cumulative variancepop aggregation function",
        title="function-cumulativevariancepop",
    )

    def build_agg(self) -> FuncAggBase:
        return FuncVariancePop(args=self.args)


class FuncCumulativeCount(FuncCumulativeBase):
    fun: Literal["cumulativecount"] = Field(
        default="cumulativecount",
        description="Cumulative count aggregation function",
        title="function-cumulativecount",
    )

    def build_agg(self) -> FuncAggBase:
        return FuncCount(args=self.args)


class FuncCumulativeCountDistinct(FuncCumulativeBase):
    fun: Literal["cumulativecountdistinct"] = Field(
        default="cumulativecountdistinct",
        description="Cumulative count distinct aggregation function",
        title="function-cumulativecountdistinct",
    )

    def build_agg(self) -> FuncAggBase:
        return FuncCountDistinct(args=self.args)


class FuncCumulativeSumBoolean(FuncCumulativeBase):
    fun: Literal["cumulativesumboolean"] = Field(
        default="cumulativesumboolean",
        description="Cumulative sum boolean aggregation function",
        title="function-cumulativesumboolean",
    )

    def build_agg(self) -> FuncAggBase:
        return FuncSumBoolean(args=self.args)
