from __future__ import annotations

from datetime import date, datetime
from typing import Any

from hex_sl_utils._vendor.sqlglot import exp
from hex_sl_utils.calc.compiled import (
    ExpressionContext,
    ExpressionKind,
    TypedSelectExpression,
    datatype_to_sqlglot,
    needs_parens_for_substitution,
)
from hex_sl_utils.calc.visitor import _extract_hexsl_calc_string
from hex_sl_utils.types import DataType


class TestDialect:
    """Small dialect adapter used to test the extracted compiler boundary."""

    def name(self) -> str:
        return "test"

    def sqlglot_dialect(self) -> str:
        return "duckdb"

    def __getattr__(self, name: str) -> Any:
        msg = f"Test dialect service not implemented: {name}"
        raise NotImplementedError(msg)

    def compile_literal(
        self, value: float | str | bool | date | datetime | None
    ) -> TypedSelectExpression:
        if value is None:
            expression = exp.Null()
            data_type = DataType.NULL
        elif isinstance(value, bool):
            expression = exp.Boolean(this=value)
            data_type = DataType.BOOLEAN
        elif isinstance(value, (int, float)):
            expression = exp.Literal.number(value)
            data_type = DataType.NUMBER
        elif isinstance(value, datetime):
            expression = exp.Cast(
                this=exp.Literal.string(value.isoformat()),
                to=datatype_to_sqlglot(DataType.TIMESTAMP_NAIVE),
            )
            data_type = DataType.TIMESTAMP_NAIVE
        elif isinstance(value, date):
            expression = exp.Cast(
                this=exp.Literal.string(value.isoformat()),
                to=datatype_to_sqlglot(DataType.DATE),
            )
            data_type = DataType.DATE
        else:
            expression = exp.Literal.string(value)
            data_type = DataType.STRING

        return TypedSelectExpression.from_sqlglot(
            expression, data_type, ExpressionKind.SCALAR
        )

    def func(self, name: str, *args: Any) -> exp.Func:
        return exp.Anonymous(this=name, expressions=list(args))

    def wrap_expression_for_context(
        self, expression: TypedSelectExpression, context: ExpressionContext
    ) -> TypedSelectExpression:
        return expression

    def resolve_hexsl_calc_placeholders(
        self, expression: exp.Expression, **kwargs: Any
    ) -> exp.Expression:
        from hex_sl_utils.calc.ast.expr import CalcExpr
        from hex_sl_utils.calc.compiler import CalcToTypedSelectVisitor

        def resolve(node: exp.Expression) -> exp.Expression:
            calc_json = _extract_hexsl_calc_string(node)
            if calc_json is None:
                return node
            calc = CalcExpr.model_validate_json(calc_json)
            visitor = CalcToTypedSelectVisitor(
                dialect=self,
                context=kwargs["context"],
                schema=kwargs["schema"],
                timezone=kwargs["timezone"],
                parameters=kwargs["parameters"],
                substitutions=kwargs["substitutions"],
            )
            result = calc.root.accept(visitor).expression
            if needs_parens_for_substitution(result):
                return exp.Paren(this=result)
            return result

        return expression.transform(resolve)
