import pytest

from hex_sl_utils._vendor.sqlglot import exp
from hex_sl_utils.calc import (
    ExpressionContext,
    ExpressionKind,
    compile_calc_expression,
    parse_calc_expression,
)
from hex_sl_utils.calc.ast.functions.rolling import FuncRollingBase
from hex_sl_utils.calc.compiled import TypedSelectExpression, has_aggregate_function
from hex_sl_utils.calc.visitor import _extract_hexsl_calc_string
from hex_sl_utils.types import DataType

from ._dialect import TestDialect


def test_compile_calc_expression_public_api() -> None:
    expression = parse_calc_expression("price * 2 + {{tax}}")

    result = compile_calc_expression(
        expression,
        dialect=TestDialect(),
        context=ExpressionContext.PROJECTION,
        schema={"price": DataType.NUMBER},
        timezone="UTC",
        parameters={"tax": DataType.NUMBER},
        skip_mangle=True,
    )

    assert isinstance(result, TypedSelectExpression)
    assert isinstance(result.expression, exp.Expression)
    assert result.expression.__class__.__module__.startswith(
        "hex_sl_utils._vendor.sqlglot"
    )
    assert result.expression.sql(dialect="duckdb") == '"price" * 2 + $tax'
    assert result.data_type == DataType.NUMBER
    assert result.kind == ExpressionKind.COLUMN


def test_calc_expr_compile_convenience_api() -> None:
    expression = parse_calc_expression("amount + 1")

    result = expression.compile(
        TestDialect(),
        context=ExpressionContext.PROJECTION,
        schema={
            "amount": DataType.NUMBER,
        },
        timezone="UTC",
        skip_mangle=True,
    )

    assert result.expression.sql(dialect="duckdb") == '"amount" + 1'


def test_rolling_function_metadata_is_query_engine_neutral() -> None:
    expression = parse_calc_expression("cumulativesum(amount)")

    assert isinstance(expression.root, FuncRollingBase)
    assert expression.root.build_rolling().trailing == "unbounded"


def test_anonymous_percentile_functions_remain_aggregations() -> None:
    expression = exp.Anonymous(
        this="percentile_cont", expressions=[exp.column("amount")]
    )

    assert has_aggregate_function(expression)


def test_bare_identifier_remains_a_column_expression() -> None:
    result = TypedSelectExpression.from_sqlglot(
        exp.Identifier(this="amount"), DataType.NUMBER
    )

    assert result.kind == ExpressionKind.COLUMN


def test_vendored_placeholder_name_accepts_an_expression_value() -> None:
    placeholder = exp.Placeholder(this=exp.Identifier(this="amount"))

    assert placeholder.name == "amount"


def test_hexsl_calc_placeholder_preserves_value_error_contract() -> None:
    placeholder = exp.Anonymous(
        this="_HEXSL_CALC", expressions=[exp.column("not_a_literal")]
    )

    with pytest.raises(ValueError, match="requires a string literal"):
        _extract_hexsl_calc_string(placeholder)
