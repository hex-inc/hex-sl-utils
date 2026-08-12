# pyright: reportCallIssue=false, reportIncompatibleVariableOverride=false
from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Literal

from pydantic import Field
from typing_extensions import override

from hex_sl_utils._vendor.sqlglot import exp, parse_one
from hex_sl_utils.calc.ast.functions.base import FuncBase
from hex_sl_utils.calc.ast.functions.cast import FuncToBoolean
from hex_sl_utils.calc.compiled import (
    ExpressionContext,
    ExpressionKind,
    TypedSelectExpression,
)
from hex_sl_utils.calc.errors import TypeCheckError, UnsupportedByDialectError
from hex_sl_utils.types import DataType

if TYPE_CHECKING:
    from hex_sl_utils.calc.ast.args import Args  # noqa: F401
    from hex_sl_utils.calc.protocols import CalcDialect


class FuncAggBase(FuncBase):
    def is_agg(self) -> bool:
        return True

    def _validate_compute_kind(
        self, arg_exprs: list[TypedSelectExpression], context: ExpressionContext
    ) -> ExpressionKind:
        # Get and validate input expression kind
        kind = ExpressionKind._validate_infer_kind([arg.kind for arg in arg_exprs])
        if kind == ExpressionKind.WINDOW:
            msg = f"{self.fun} cannot accept a nested window expression"
            raise TypeCheckError(msg)

        # Compute output expression kind based on context
        return (
            ExpressionKind.AGGREGATION
            if context == ExpressionContext.AGGREGATION
            else ExpressionKind.WINDOW
        )

    def _build_agg_expression(
        self,
        agg_expr: exp.Expression,
        data_type: DataType,
        arg_exprs: list[TypedSelectExpression],
        context: ExpressionContext,
    ) -> TypedSelectExpression:
        """
        Build the final aggregate expression, wrapping in window function if needed.

        Args:
            agg_expr: The aggregate expression (e.g., exp.Sum, exp.Min, etc.)
            data_type: The result data type
            arg_exprs: Original argument expressions for kind validation
            context: The expression context

        Returns:
            TypedSelectExpression with proper wrapping for context
        """
        # If in window context, wrap in window function
        if context != ExpressionContext.AGGREGATION:
            window_expr = exp.Window(this=agg_expr)
            return TypedSelectExpression.from_sqlglot(
                window_expr,
                data_type,
                self._validate_compute_kind(arg_exprs, context),
            )

        return TypedSelectExpression.from_sqlglot(
            agg_expr, data_type, self._validate_compute_kind(arg_exprs, context)
        )


class FuncMin(FuncAggBase):
    fun: Literal["min"] = Field(
        default="min",
        description="Min function, as in min(col)",
        title="function-min",
    )

    @override
    def compile(
        self,
        arg_exprs: list[TypedSelectExpression],
        dialect: CalcDialect,
        context: ExpressionContext,
        tz: str,
    ) -> TypedSelectExpression:
        arg = self._validate_single_arg(arg_exprs)

        # Build MIN aggregate
        min_expr = exp.Min(this=arg.expression)

        return self._build_agg_expression(min_expr, arg.data_type, arg_exprs, context)


class FuncMax(FuncAggBase):
    fun: Literal["max"] = Field(
        default="max",
        description="Max function, as in max(col)",
        title="function-max",
    )

    @override
    def compile(
        self,
        arg_exprs: list[TypedSelectExpression],
        dialect: CalcDialect,
        context: ExpressionContext,
        tz: str,
    ) -> TypedSelectExpression:
        arg = self._validate_single_arg(arg_exprs)

        # Build MAX aggregate
        max_expr = exp.Max(this=arg.expression)

        return self._build_agg_expression(max_expr, arg.data_type, arg_exprs, context)


class FuncAvg(FuncAggBase):
    fun: Literal["avg"] = Field(
        default="avg",
        description="Avg function, as in avg(col)",
        title="function-avg",
    )

    @override
    def compile(
        self,
        arg_exprs: list[TypedSelectExpression],
        dialect: CalcDialect,
        context: ExpressionContext,
        tz: str,
    ) -> TypedSelectExpression:
        arg = self._validate_single_arg(arg_exprs, DataType.NUMBER)

        # Cast to DOUBLE using dialect method
        cast_typed = dialect.cast_to_float(arg)

        # Build AVG aggregate
        avg_expr = exp.Avg(this=cast_typed.expression)

        return self._build_agg_expression(avg_expr, DataType.NUMBER, arg_exprs, context)


class FuncCount(FuncAggBase):
    fun: Literal["count"] = Field(
        default="count",
        description="Count function, as in count(col)",
        title="function-count",
    )

    @override
    def compile(
        self,
        arg_exprs: list[TypedSelectExpression],
        dialect: CalcDialect,
        context: ExpressionContext,
        tz: str,
    ) -> TypedSelectExpression:
        if len(arg_exprs) == 0:
            if (
                context == ExpressionContext.PROJECTION
                and dialect.use_empty_over_for_count_star_window_function()
            ):
                sge = parse_one("COUNT(*) OVER ()", dialect=dialect.sqlglot_dialect())
                return TypedSelectExpression.from_sqlglot(
                    sge,
                    DataType.NUMBER,
                    self._validate_compute_kind(arg_exprs, context),
                )
            else:
                one_literal = dialect.compile_literal(1)
                count_expr = exp.Count(this=one_literal.expression)
                return self._build_agg_expression(
                    count_expr, DataType.NUMBER, arg_exprs, context
                )
        else:
            # COUNT(arg)
            count_expr = exp.Count(this=arg_exprs[0].expression)
            return self._build_agg_expression(
                count_expr, DataType.NUMBER, arg_exprs, context
            )


class FuncSum(FuncAggBase):
    fun: Literal["sum"] = Field(
        default="sum",
        description="Sum function, as in sum(col)",
        title="function-sum",
    )

    @override
    def compile(
        self,
        arg_exprs: list[TypedSelectExpression],
        dialect: CalcDialect,
        context: ExpressionContext,
        tz: str,
    ) -> TypedSelectExpression:
        arg = self._validate_single_arg(arg_exprs, DataType.NUMBER)

        # Build SUM aggregate
        sum_expr = exp.Sum(this=arg.expression)

        return self._build_agg_expression(sum_expr, DataType.NUMBER, arg_exprs, context)


class FuncSumBoolean(FuncAggBase):
    fun: Literal["sumboolean"] = Field(
        default="sumboolean",
        description="SumBoolean function, as in sumboolean(col)",
        title="function-sumboolean",
    )

    @override
    def compile(
        self,
        arg_exprs: list[TypedSelectExpression],
        dialect: CalcDialect,
        context: ExpressionContext,
        tz: str,
    ) -> TypedSelectExpression:
        arg = FuncToBoolean._compile_to_boolean(arg_exprs[0], dialect)

        # Convert boolean to 1 or 0
        one_literal = dialect.compile_literal(1)
        zero_literal = dialect.compile_literal(0)
        bool_as_int = dialect.build_ifelse(arg, one_literal, zero_literal)

        # Build SUM aggregate on the 1/0 values
        sum_expr = exp.Sum(this=bool_as_int.expression)

        return self._build_agg_expression(sum_expr, DataType.NUMBER, arg_exprs, context)


class FuncStddev(FuncAggBase):
    fun: Literal["stddev"] = Field(
        default="stddev",
        description="Stddev function, as in stddev(col)",
        title="function-stddev",
    )

    @override
    def compile(
        self,
        arg_exprs: list[TypedSelectExpression],
        dialect: CalcDialect,
        context: ExpressionContext,
        tz: str,
    ) -> TypedSelectExpression:
        arg = self._validate_single_arg(arg_exprs, DataType.NUMBER)

        # Cast to float64 first using dialect method
        cast_typed = dialect.cast_to_float(arg)

        # Build STDDEV_SAMP aggregate (sample standard deviation)
        stddev_expr = exp.StddevSamp(this=cast_typed.expression)

        return self._build_agg_expression(
            stddev_expr, DataType.NUMBER, arg_exprs, context
        )


class FuncStddevPop(FuncAggBase):
    fun: Literal["stddevpop"] = Field(
        default="stddevpop",
        description="StddevPop function, as in stddevpop(col)",
        title="function-stddevpop",
    )

    @override
    def compile(
        self,
        arg_exprs: list[TypedSelectExpression],
        dialect: CalcDialect,
        context: ExpressionContext,
        tz: str,
    ) -> TypedSelectExpression:
        arg = self._validate_single_arg(arg_exprs, DataType.NUMBER)

        # Cast to float64 first using dialect method
        cast_typed = dialect.cast_to_float(arg)

        # Build STDDEV_POP aggregate (population standard deviation)
        stddev_expr = exp.StddevPop(this=cast_typed.expression)

        return self._build_agg_expression(
            stddev_expr, DataType.NUMBER, arg_exprs, context
        )


class FuncVariance(FuncAggBase):
    fun: Literal["variance"] = Field(
        default="variance",
        description="Variance function, as in variance(col)",
        title="function-variance",
    )

    @override
    def compile(
        self,
        arg_exprs: list[TypedSelectExpression],
        dialect: CalcDialect,
        context: ExpressionContext,
        tz: str,
    ) -> TypedSelectExpression:
        arg = self._validate_single_arg(arg_exprs, DataType.NUMBER)

        # Cast to float64 first using dialect method
        cast_typed = dialect.cast_to_float(arg)

        # Build VAR_SAMP aggregate (sample variance)
        var_expr = exp.Variance(this=cast_typed.expression)

        return self._build_agg_expression(var_expr, DataType.NUMBER, arg_exprs, context)


class FuncVariancePop(FuncAggBase):
    fun: Literal["variancepop"] = Field(
        default="variancepop",
        description="VariancePop function, as in variancepop(col)",
        title="function-variancepop",
    )

    @override
    def compile(
        self,
        arg_exprs: list[TypedSelectExpression],
        dialect: CalcDialect,
        context: ExpressionContext,
        tz: str,
    ) -> TypedSelectExpression:
        arg = self._validate_single_arg(arg_exprs, DataType.NUMBER)

        # Cast to float64 first using dialect method
        cast_typed = dialect.cast_to_float(arg)

        # Build VAR_POP aggregate (population variance)
        var_expr = exp.VariancePop(this=cast_typed.expression)

        return self._build_agg_expression(var_expr, DataType.NUMBER, arg_exprs, context)


class FuncMedian(FuncAggBase):
    fun: Literal["median"] = Field(
        default="median",
        description="Median function, as in median(col)",
        title="function-median",
    )

    @override
    def compile(
        self,
        arg_exprs: list[TypedSelectExpression],
        dialect: CalcDialect,
        context: ExpressionContext,
        tz: str,
    ) -> TypedSelectExpression:
        if not dialect.supports_median():
            msg = f"{self.fun} is not supported by {dialect.name()}"
            raise UnsupportedByDialectError(msg)
        arg = self._validate_single_arg(arg_exprs, DataType.NUMBER)

        # Use dialect's build_median method
        median_expr_typed = dialect.build_median(arg)

        return self._build_agg_expression(
            median_expr_typed.expression, DataType.NUMBER, arg_exprs, context
        )


class FuncPercentileBase(FuncAggBase):
    expected_arg_count: ClassVar[int] = 2

    def _arg_error_message(self, provided: int) -> str:
        return (
            f"{self.fun} requires two arguments: "
            f"a numeric expression and a percentile literal"
        )

    def _validate_value_and_percentile(
        self, arg_exprs: list[TypedSelectExpression]
    ) -> tuple[TypedSelectExpression, float]:
        value_expr = arg_exprs[0]
        if value_expr.data_type != DataType.NUMBER:
            msg = f"{self.fun} requires the input expression to be a number"
            raise TypeCheckError(msg)

        percentile_expr = arg_exprs[1]
        if percentile_expr.data_type != DataType.NUMBER:
            msg = f"{self.fun} requires the percentile argument to be numeric"
            raise TypeCheckError(msg)

        percentile_node = percentile_expr.expression
        if not (isinstance(percentile_node, exp.Literal) and percentile_node.is_number):
            msg = (
                f"{self.fun} percentile value must be a numeric literal between 0 and 1"
            )
            raise TypeCheckError(msg)

        percentile_value = float(percentile_node.this)
        if not 0 <= percentile_value <= 1:
            msg = f"{self.fun} percentile value must be between 0 and 1"
            raise TypeCheckError(msg)

        return value_expr, percentile_value


class FuncPercentile(FuncPercentileBase):
    fun: Literal["percentile"] = Field(
        default="percentile",
        description="Exact percentile function, as in percentile(col, 0.95)",
        title="function-percentile",
    )

    @override
    def compile(
        self,
        arg_exprs: list[TypedSelectExpression],
        dialect: CalcDialect,
        context: ExpressionContext,
        tz: str,
    ) -> TypedSelectExpression:
        if len(arg_exprs) != self.expected_arg_count:
            msg = self._arg_error_message(len(arg_exprs))
            raise TypeCheckError(msg)

        value_expr, percentile_value = self._validate_value_and_percentile(arg_exprs)

        if not dialect.supports_percentile_exact():
            msg = f"{self.fun} is not supported by {dialect.name()}"
            raise UnsupportedByDialectError(msg)

        percentile_typed = dialect.build_percentile_exact(value_expr, percentile_value)

        return self._build_agg_expression(
            percentile_typed.expression, DataType.NUMBER, arg_exprs, context
        )


class FuncPercentileApprox(FuncPercentileBase):
    fun: Literal["percentileapprox"] = Field(
        default="percentileapprox",
        description=(
            "Approximate percentile function, as in percentileapprox(col, 0.95)"
        ),
        title="function-percentileapprox",
    )

    @override
    def compile(
        self,
        arg_exprs: list[TypedSelectExpression],
        dialect: CalcDialect,
        context: ExpressionContext,
        tz: str,
    ) -> TypedSelectExpression:
        if len(arg_exprs) != self.expected_arg_count:
            msg = self._arg_error_message(len(arg_exprs))
            raise TypeCheckError(msg)

        value_expr, percentile_value = self._validate_value_and_percentile(arg_exprs)

        if not dialect.supports_percentile_approx():
            msg = f"{self.fun} is not supported by {dialect.name()}"
            raise UnsupportedByDialectError(msg)

        percentile_typed = dialect.build_percentile_approx(value_expr, percentile_value)

        return self._build_agg_expression(
            percentile_typed.expression, DataType.NUMBER, arg_exprs, context
        )


class FuncCountDistinct(FuncAggBase):
    fun: Literal["countdistinct"] = Field(
        default="countdistinct",
        description="CountDistinct function, as in countdistinct(col)",
        title="function-countdistinct",
    )

    @override
    def compile(
        self,
        arg_exprs: list[TypedSelectExpression],
        dialect: CalcDialect,
        context: ExpressionContext,
        tz: str,
    ) -> TypedSelectExpression:
        arg = self._validate_single_arg(arg_exprs)

        # Build COUNT(DISTINCT arg) aggregate using Distinct node
        distinct_expr = exp.Distinct(expressions=[arg.expression])
        count_distinct_expr = exp.Count(this=distinct_expr)

        return self._build_agg_expression(
            count_distinct_expr, DataType.NUMBER, arg_exprs, context
        )
