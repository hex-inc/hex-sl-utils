# pyright: reportIncompatibleVariableOverride=false

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import Field

from hex_sl_utils._vendor.sqlglot import exp
from hex_sl_utils.calc.ast.functions.base import FuncBase
from hex_sl_utils.datatype import DataType
from hex_sl_utils.expr import ExpressionContext, TypedSelectExpression

# Union type for all unary math function names - helps ensure func_map completeness
UnaryMathFunction = Literal[
    "sqrt", "abs", "round", "floor", "ceil", "exp", "sin", "cos", "tan", "cot"
]

if TYPE_CHECKING:
    from hex_sl_utils.dialect.dialect import Dialect


class FuncUnaryMathBase(FuncBase):
    """Base class for unary math functions"""

    fun: UnaryMathFunction

    def inputs_float(self) -> bool:
        return False

    def compile(
        self,
        arg_exprs: list[TypedSelectExpression],
        dialect: Dialect,
        context: ExpressionContext,
        tz: str,
    ) -> TypedSelectExpression:
        """
        Default compilation for unary math functions
        """
        arg = self._validate_single_arg(arg_exprs, DataType.NUMBER)

        # Cast to float64 if needed
        expr = arg.expression
        if self.inputs_float():
            expr = exp.Cast(this=expr, to=exp.DataType.build("DOUBLE"))

        # Map some function names to sqlglot classes
        func_map: dict[UnaryMathFunction, type[exp.Expression]] = {
            "sqrt": exp.Sqrt,
            "abs": exp.Abs,
            "round": exp.Round,
            "floor": exp.Floor,
            "ceil": exp.Ceil,
            "exp": exp.Exp,
        }

        func_class = func_map.get(self.fun)
        if func_class:
            result_expr = func_class(this=expr)
        else:
            # Use dialect.func for trig functions and others
            result_expr = dialect.func(self.fun.upper(), expr)

        return TypedSelectExpression.from_sqlglot(
            result_expr, DataType.NUMBER, arg.kind
        )


class FuncSqrt(FuncUnaryMathBase):
    fun: Literal["sqrt"] = Field(
        default="sqrt",
        description="Sqrt function, as in sqrt(4) = 2",
        title="function-sqrt",
    )

    def inputs_float(self) -> bool:
        return True


class FuncAbs(FuncUnaryMathBase):
    fun: Literal["abs"] = Field(
        default="abs",
        description="Absolute value function, as in abs(-1) = 1",
        title="function-abs",
    )


class FuncRound(FuncUnaryMathBase):
    fun: Literal["round"] = Field(
        default="round",
        description="Round function, as in round(3.14159) = 3",
        title="function-round",
    )

    def compile(
        self,
        arg_exprs: list[TypedSelectExpression],
        dialect: Dialect,
        context: ExpressionContext,
        tz: str,
    ) -> TypedSelectExpression:
        """
        Custom implementation that uses dialect's build_round method
        """
        arg = self._validate_single_arg(arg_exprs, DataType.NUMBER)
        return dialect.build_round(arg)


class FuncFloor(FuncUnaryMathBase):
    fun: Literal["floor"] = Field(
        default="floor",
        description="Floor function, as in floor(3.14159) = 3",
        title="function-floor",
    )

    def inputs_float(self) -> bool:
        return True


class FuncCeil(FuncUnaryMathBase):
    fun: Literal["ceil"] = Field(
        default="ceil",
        description="Ceil function, as in ceil(3.14159) = 4",
        title="function-ceil",
    )

    def inputs_float(self) -> bool:
        return True


class FuncExp(FuncUnaryMathBase):
    fun: Literal["exp"] = Field(
        default="exp",
        description="Exponential function, as in exp(1) = 2.71828",
        title="function-exp",
    )

    def inputs_float(self) -> bool:
        return True


class FuncSin(FuncUnaryMathBase):
    fun: Literal["sin"] = Field(
        default="sin",
        description="Sin function, as in sin(π/2) = 1",
        title="function-sin",
    )

    def inputs_float(self) -> bool:
        return True


class FuncCos(FuncUnaryMathBase):
    fun: Literal["cos"] = Field(
        default="cos",
        description="Cos function, as in cos(0) = 1",
        title="function-cos",
    )

    def inputs_float(self) -> bool:
        return True


class FuncTan(FuncUnaryMathBase):
    fun: Literal["tan"] = Field(
        default="tan",
        description="Tan function, as in tan(π/4) = 1",
        title="function-tan",
    )

    def inputs_float(self) -> bool:
        return True


class FuncCot(FuncUnaryMathBase):
    fun: Literal["cot"] = Field(
        default="cot",
        description="Cot function, as in cot(π/4) = 1",
        title="function-cot",
    )

    def compile(
        self,
        arg_exprs: list[TypedSelectExpression],
        dialect: Dialect,
        context: ExpressionContext,
        tz: str,
    ) -> TypedSelectExpression:
        """
        Custom implementation that handles cot(0) -> None and fallback to 1/tan(x)
        """
        arg = self._validate_single_arg(arg_exprs, DataType.NUMBER)

        # Build condition: arg == 0
        zero_literal = dialect.compile_literal(0)
        is_zero = TypedSelectExpression.from_sqlglot(
            exp.EQ(this=arg.expression, expression=zero_literal.expression),
            DataType.BOOLEAN,
            arg.kind,
        )

        # Cast to float64
        cast_expr = exp.Cast(this=arg.expression, to=exp.DataType.build("DOUBLE"))

        # Build COT expression or fallback to 1 / TAN(x)
        if dialect.supports_cot_function():
            cot_expr = TypedSelectExpression.from_sqlglot(
                dialect.func("COT", cast_expr), DataType.NUMBER, arg.kind
            )
        else:
            # Fallback to 1 / TAN(x) for dialects that don't support COT
            tan_expr = dialect.func("TAN", cast_expr)
            one_literal = exp.Literal.number(1.0)
            cot_expr = TypedSelectExpression.from_sqlglot(
                exp.Div(this=one_literal, expression=tan_expr),
                DataType.NUMBER,
                arg.kind,
            )

        # Build NULL literal
        null_literal = dialect.build_null(DataType.NUMBER)

        # Use dialect's build_ifelse: if arg == 0 then NULL else cot(arg)
        return dialect.build_ifelse(is_zero, null_literal, cot_expr)
