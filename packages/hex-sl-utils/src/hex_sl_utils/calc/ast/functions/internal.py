"""Internal chart functions for type conversions."""

# pyright: reportIncompatibleVariableOverride=false

from typing import TYPE_CHECKING, Literal

from pydantic import Field

from hex_sl_utils._vendor.sqlglot import exp
from hex_sl_utils.calc.ast.functions.base import FuncBase
from hex_sl_utils.datatype import DataType
from hex_sl_utils.expr import ExpressionContext, TypedSelectExpression

if TYPE_CHECKING:
    from hex_sl_utils.calc.ast.args import Args  # noqa: F401
    from hex_sl_utils.dialect.dialect import Dialect


class FuncChartToNumber(FuncBase):
    """Internal function to convert values to numbers based on their type."""

    fun: Literal["_chart_tonumber"] = Field(
        default="_chart_tonumber",
        description="Internal chart function to convert to number based on type",
        title="function-_chart_tonumber",
    )

    def compile(
        self,
        arg_exprs: list[TypedSelectExpression],
        dialect: "Dialect",
        context: ExpressionContext,
        tz: str,
    ) -> TypedSelectExpression:
        arg = self._validate_single_arg(arg_exprs)
        arg_type = arg.data_type

        if arg_type == DataType.STRING:
            # STRING → tonumber
            return dialect.cast_str_to_number(arg)
        elif arg_type in (DataType.DATE, DataType.TIMESTAMP, DataType.TIMESTAMPTZ):
            # DATE/TIMESTAMP/TIMESTAMPTZ → datetimetoepochms
            return dialect.datetime_to_epoch_ms(arg)
        elif arg_type == DataType.BOOLEAN:
            # BOOLEAN → if(expr, 1, 0)
            one_literal = dialect.compile_literal(1)
            zero_literal = dialect.compile_literal(0)
            return dialect.build_ifelse(arg, one_literal, zero_literal)
        elif arg_type == DataType.NUMBER:
            # NUMBER → no-op
            return arg
        else:
            # For OTHER or unknown types, try regular cast to number
            return TypedSelectExpression.from_sqlglot(
                exp.Cast(this=arg.expression, to=exp.DataType.build("DOUBLE")),
                DataType.NUMBER,
                arg.kind,
            )


class FuncChartToDatetime(FuncBase):
    """Internal function to convert values to datetime based on their type."""

    fun: Literal["_chart_todatetime"] = Field(
        default="_chart_todatetime",
        description="Internal chart function to convert to datetime based on type",
        title="function-_chart_todatetime",
    )

    def compile(
        self,
        arg_exprs: list[TypedSelectExpression],
        dialect: "Dialect",
        context: ExpressionContext,
        tz: str,
    ) -> TypedSelectExpression:
        arg = self._validate_single_arg(arg_exprs)
        arg_type = arg.data_type

        if arg_type == DataType.STRING:
            # STRING → todatetime
            return dialect.cast_str_to_timestamp(arg, tz)
        elif arg_type == DataType.NUMBER:
            # NUMBER → epochmstodatetime
            return dialect.epoch_ms_to_timestamp(arg)
        elif arg_type == DataType.BOOLEAN:
            # BOOLEAN → epochmstodatetime(if(expr, 1, 0))
            one_literal = dialect.compile_literal(1)
            zero_literal = dialect.compile_literal(0)
            if_expr = dialect.build_ifelse(arg, one_literal, zero_literal)
            return dialect.epoch_ms_to_timestamp(if_expr)
        elif arg_type in (DataType.TIMESTAMP, DataType.TIMESTAMPTZ, DataType.DATE):
            # DATE/TIMESTAMP/TIMESTAMPTZ → no-op (but convert DATE to TIMESTAMP)
            if arg_type == DataType.DATE:
                return dialect.cast_date_to_timestamp(arg)
            return arg
        else:
            # For OTHER or unknown types, try regular cast to timestamp
            return TypedSelectExpression.from_sqlglot(
                exp.Cast(this=arg.expression, to=exp.DataType.build("TIMESTAMP")),
                DataType.TIMESTAMP,
                arg.kind,
            )
