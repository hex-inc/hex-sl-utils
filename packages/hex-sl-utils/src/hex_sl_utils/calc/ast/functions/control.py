from typing import Literal

from pydantic import Field

from hex_sl.calc.ast.args import Args
from hex_sl.calc.ast.functions.base import FuncBase
from hex_sl.calc.ast.functions.cast import (
    FuncToBoolean,
    FuncToDate,
    FuncToNumber,
    FuncToText,
)
from hex_sl.datatype import DataType
from hex_sl.dialect.base import HexSLDialect
from hex_sl.expr import ExpressionContext, ExpressionKind, TypedSelectExpression
from hex_sl.utils import TypeCheckError

_ISONEOF_COERCION_MAP: dict[DataType, type[FuncBase]] = {
    DataType.NUMBER: FuncToNumber,
    DataType.STRING: FuncToText,
    DataType.BOOLEAN: FuncToBoolean,
    DataType.DATE: FuncToDate,
}


class FuncIf(FuncBase):
    """If(pred, true_expr, false_expr) function"""

    fun: Literal["if"] = Field(
        default="if",
        description=("If function, as in if(4 > 0, 1, -1) = 1"),
        title="function-if",
    )

    def compile(
        self,
        arg_exprs: list[TypedSelectExpression],
        dialect: HexSLDialect,
        context: ExpressionContext,
        tz: str,
    ) -> TypedSelectExpression:
        pred, true_expr, false_expr = self._validate_n_args(arg_exprs, 3)

        if not pred.data_type == DataType.BOOLEAN:
            msg = (
                "First argumnet to if function must be a boolean, received: "
                f"{pred.data_type}"
            )
            raise TypeCheckError(msg)

        if (
            true_expr.data_type != DataType.NULL
            and false_expr.data_type != DataType.NULL
            and true_expr.data_type != false_expr.data_type
        ):
            msg = (
                "Second and third arguments to the if function must have "
                "the same type, received: "
                f"{true_expr.data_type} and {false_expr.data_type}"
            )
            raise TypeCheckError(msg)

        return dialect.build_ifelse(pred, true_expr, false_expr)


class FuncIsNull(FuncBase):
    """IsNull(expr) function"""

    fun: Literal["isnull"] = Field(
        default="isnull",
        description=("IsNull function, as in isnull(null) = true"),
        title="function-isnull",
    )

    def compile(
        self,
        arg_exprs: list[TypedSelectExpression],
        dialect: HexSLDialect,
        context: ExpressionContext,
        tz: str,
    ) -> TypedSelectExpression:
        arg = self._validate_single_arg(arg_exprs)

        return dialect.build_isnull(arg)


class FuncCoalesce(FuncBase):
    """Coalesce(expr, ...) function"""

    fun: Literal["coalesce"] = Field(
        default="coalesce",
        description=("Coalesce function, as in coalesce(null, 1, -1) = 1"),
        title="function-coalesce",
    )

    def compile(
        self,
        arg_exprs: list[TypedSelectExpression],
        dialect: HexSLDialect,
        context: ExpressionContext,
        tz: str,
    ) -> TypedSelectExpression:
        self._validate_variadic_with_same_type(arg_exprs, allow_empty=False)

        return dialect.build_coalesce(*arg_exprs)


class FuncIsFinite(FuncBase):
    """IsFinite(expr) function"""

    fun: Literal["isfinite"] = Field(
        default="isfinite",
        description=("IsFinite function, as in isfinite(1.0) = true"),
        title="function-isfinite",
    )

    def compile(
        self,
        arg_exprs: list[TypedSelectExpression],
        dialect: HexSLDialect,
        context: ExpressionContext,
        tz: str,
    ) -> TypedSelectExpression:
        from hex_sl._vendor.sqlglot import exp

        arg = self._validate_single_arg(arg_exprs)

        if arg.data_type == DataType.NUMBER and dialect.supports_non_finite_floats():
            # Build: NOT (IS NULL OR IS NAN OR IS INFINITE)
            isnull = dialect.build_isnull(arg)
            isnan = dialect.build_isnan(arg)
            isinf = dialect.build_isinf(arg)

            # Combine with OR and negate the result
            return TypedSelectExpression.from_sqlglot(
                exp.Not(
                    this=exp.Paren(
                        this=exp.Or(
                            this=exp.Or(
                                this=isnull.expression, expression=isnan.expression
                            ),
                            expression=isinf.expression,
                        )
                    )
                ),
                DataType.BOOLEAN,
                arg.kind,
            )
        else:
            # Same as !IsNull for non-numbers, and for dialects that don't support
            # isinf/isnan checks
            isnull = dialect.build_isnull(arg)
            return TypedSelectExpression.from_sqlglot(
                exp.Not(this=isnull.expression), DataType.BOOLEAN, arg.kind
            )


class FuncIsOneOf(FuncBase):
    """IsOneOf(expr, option1, option2, ...) function"""

    fun: Literal["isoneof"] = Field(
        default="isoneof",
        description=("IsOneOf function, as in isoneof(1, 2, 1) = true"),
        title="function-isoneof",
    )

    def compile(
        self,
        arg_exprs: list[TypedSelectExpression],
        dialect: HexSLDialect,
        context: ExpressionContext,
        tz: str,
    ) -> TypedSelectExpression:
        from hex_sl._vendor.sqlglot import exp

        if len(arg_exprs) < 1:
            msg = f"Expected at least 1 argument for {self.fun}, got {len(arg_exprs)}"
            raise TypeCheckError(msg)

        value_expr = arg_exprs[0]
        target_type = value_expr.data_type

        # No options → always false
        if len(arg_exprs) == 1:
            return dialect.compile_literal(False)

        # Second and following args must be scalars
        for arg in arg_exprs[1:]:
            if arg.kind != ExpressionKind.SCALAR:
                msg = "All arguments to IsOneOf, after the first, must be scalars"
                raise TypeCheckError(msg)

        # Coerce option args to match the target type
        coerced_options: list[TypedSelectExpression] = []
        for arg in arg_exprs[1:]:
            if arg.data_type == target_type or arg.data_type == DataType.NULL:
                coerced_options.append(arg)
            else:
                converter_cls = _ISONEOF_COERCION_MAP.get(target_type)
                if converter_cls is None:
                    msg = (
                        f"Cannot auto-coerce arguments for {self.fun}: "
                        f"no converter available for target type {target_type.name}"
                    )
                    raise TypeCheckError(msg)
                converter = converter_cls(args=Args(root=[]))
                coerced = converter.compile([arg], dialect, context, tz)
                # Boolean coercion produces predicates (e.g. arg != 0) which are
                # not valid scalar values inside IN lists on MSSQL. Wrap for
                # PROJECTION context to convert predicates to scalar integers.
                if target_type == DataType.BOOLEAN:
                    coerced = dialect.wrap_expression_for_context(
                        coerced, ExpressionContext.PROJECTION
                    )
                coerced_options.append(coerced)

        # Build IN expression
        option_exprs = [arg.expression for arg in coerced_options]
        in_expr = exp.In(this=value_expr.expression, expressions=option_exprs)

        return TypedSelectExpression.from_sqlglot(
            in_expr, DataType.BOOLEAN, value_expr.kind
        )


class FuncSwitch(FuncBase):
    """Switch(expr, case1, result1, case2, result2, ..., default) function"""

    fun: Literal["switch"] = Field(
        default="switch",
        description=("Switch function, as in switch(2, 1, 'A', 2, 'B', 3, 'C') = 'B'"),
        title="function-switch",
    )

    def compile(
        self,
        arg_exprs: list[TypedSelectExpression],
        dialect: HexSLDialect,
        context: ExpressionContext,
        tz: str,
    ) -> TypedSelectExpression:
        if len(arg_exprs) < 3:
            msg = "switch function requires at least 3 arguments"
            raise TypeCheckError(msg)

        value: TypedSelectExpression = arg_exprs[0]
        cases: list[TypedSelectExpression] = []
        results: list[TypedSelectExpression] = []

        # Process pairs of (condition, result)
        for i in range(1, len(arg_exprs) - 1, 2):
            case_expr = arg_exprs[i]
            cases.append(case_expr)
            results.append(arg_exprs[i + 1])

        # Handle default case
        default = arg_exprs[-1] if len(arg_exprs) % 2 == 0 else None

        # Ensure all results (including default) have the same type
        result_type = results[0].data_type
        for result in results + ([default] if default else []):
            if result_type == DataType.NULL:
                result_type = result.data_type
            elif result.data_type != DataType.NULL and result.data_type != result_type:
                msg = (
                    f"All results in switch must have the same type, "
                    f"got {result.data_type} and {result_type}"
                )
                raise TypeCheckError(msg)

        # Ensure that first arg and all cases have the same type
        for case_expr in cases:
            if value.data_type != case_expr.data_type:
                msg = (
                    f"First argument to switch must have the same type as all "
                    f"cases, got {value.data_type} and {cases[0].data_type}"
                )
                raise TypeCheckError(msg)

        # Build case conditions
        from hex_sl._vendor.sqlglot import exp

        conditions = []
        for i in range(len(cases)):
            # Build equality condition: value == case
            eq_expr = TypedSelectExpression.from_sqlglot(
                exp.EQ(this=value.expression, expression=cases[i].expression),
                DataType.BOOLEAN,
                value.kind,
            )
            conditions.append((eq_expr, results[i]))

        # Use dialect's build_case method
        return dialect.build_case(conditions, default)
