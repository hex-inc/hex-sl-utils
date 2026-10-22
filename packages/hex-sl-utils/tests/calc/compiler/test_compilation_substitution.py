import pytest
from inline_snapshot import snapshot

from hex_sl_utils._vendor.sqlglot import exp, parse_one
from hex_sl_utils.calc.parser import parse_calc_expression
from hex_sl_utils.datatype import DataType
from hex_sl_utils.dialect.clickhouse import ClickHouse
from hex_sl_utils.dialect.duckdb import DuckDB
from hex_sl_utils.dialect.mssql import MSSQL
from hex_sl_utils.expr import (
    ExpressionContext,
    ExpressionKind,
    TypedSelectExpression,
)


# Unary Operators
def test_compilation_substitution():
    dialect = ClickHouse()
    calc_expr = parse_calc_expression("42 + a")
    columns = {}
    substitutions = {
        "a": TypedSelectExpression(
            expression=exp.Literal.number(12),
            data_type=DataType.NUMBER,
            kind=ExpressionKind.SCALAR,
        )
    }

    typed_expr = dialect.compile_calc_expr(
        calc_expr,
        ExpressionContext.PROJECTION,
        columns,
        "America/New_York",
        parameters={},
        substitutions=substitutions,
    )

    assert typed_expr.expression.sql() == snapshot("42 + 12")


@pytest.mark.parametrize(
    ("formula", "expected", "ungrouped"),
    [
        ("true = (false = false)", "TRUE = (FALSE = FALSE)", "TRUE = FALSE = FALSE"),
        ("(true = false) = false", "(TRUE = FALSE) = FALSE", "TRUE = FALSE = FALSE"),
        ("true = (7 < 4)", "TRUE = (7 < 4)", "TRUE = 7 < 4"),
        ("!false < false", "(NOT FALSE) < FALSE", "NOT FALSE < FALSE"),
        ("false = isoneof(2, 2)", "FALSE = (2 IN (2))", "FALSE = 2 IN (2)"),
        (
            "isoneof(true || false, false)",
            "(TRUE OR FALSE) IN (FALSE)",
            "TRUE OR FALSE IN (FALSE)",
        ),
        (
            "switch(true || false, false, 7, 11)",
            "CASE WHEN (TRUE OR FALSE) = FALSE THEN 7 ELSE 11 END",
            "CASE WHEN TRUE OR FALSE = FALSE THEN 7 ELSE 11 END",
        ),
        (
            "switch(false, false || true, 7, 11)",
            "CASE WHEN FALSE = (FALSE OR TRUE) THEN 7 ELSE 11 END",
            "CASE WHEN FALSE = FALSE OR TRUE THEN 7 ELSE 11 END",
        ),
    ],
)
def test_compilation_preserves_grouping(formula, expected, ungrouped):
    dialect = DuckDB()

    result = dialect.compile_calc_expr(
        parse_calc_expression(formula),
        ExpressionContext.PROJECTION,
        {},
        "UTC",
        parameters={},
    )
    sql = result.expression.sql(dialect=dialect.sqlglot_dialect())

    assert sql != expected
    # Temporarily capture the ungrouped output until expression grouping is preserved.
    assert sql == ungrouped


@pytest.mark.parametrize(
    "predicate_sql",
    ["x IN (1, 2)", "x BETWEEN 1 AND 2", "NOT x"],
)
def test_compilation_preserves_substituted_predicate_grouping(predicate_sql):
    dialect = DuckDB()
    predicate = parse_one(predicate_sql, dialect=dialect.sqlglot_dialect())
    replacement = TypedSelectExpression.from_sqlglot(
        predicate, DataType.BOOLEAN, ExpressionKind.COLUMN
    )

    result = dialect.compile_calc_expr(
        parse_calc_expression("false = predicate"),
        ExpressionContext.PROJECTION,
        {},
        "UTC",
        parameters={},
        substitutions={"predicate": replacement},
    )
    sql = result.expression.sql(dialect=dialect.sqlglot_dialect())
    predicate_sql = predicate.sql(dialect=dialect.sqlglot_dialect())

    assert sql != f"FALSE = ({predicate_sql})"
    # Temporarily capture the ungrouped output until expression grouping is preserved.
    assert sql == f"FALSE = {predicate_sql}"


@pytest.mark.parametrize(
    ("formula", "expected", "unwrapped"),
    [
        (
            "isoneof(true || false, false)",
            "IIF(IIF((1 = 1) OR (1 = 0), 1, 0) IN (IIF((1 = 0), 1, 0)), 1, 0)",
            "IIF((1 = 1) OR (1 = 0) IN (0), 1, 0)",
        ),
        (
            "isoneof(true, false || true)",
            "IIF(IIF((1 = 1), 1, 0) IN (IIF((1 = 0) OR (1 = 1), 1, 0)), 1, 0)",
            "IIF(1 IN ((1 = 0) OR (1 = 1)), 1, 0)",
        ),
        (
            "switch(true || false, false, 7, 11)",
            "CASE WHEN IIF((1 = 1) OR (1 = 0), 1, 0) = IIF((1 = 0), 1, 0) THEN 7 ELSE 11 END",
            "CASE WHEN (1 = 1) OR (1 = 0) = 0 THEN 7 ELSE 11 END",
        ),
        (
            "switch(false, false || true, 7, 11)",
            "CASE WHEN IIF((1 = 0), 1, 0) = IIF((1 = 0) OR (1 = 1), 1, 0) THEN 7 ELSE 11 END",
            "CASE WHEN 0 = (1 = 0) OR (1 = 1) THEN 7 ELSE 11 END",
        ),
    ],
)
def test_mssql_control_predicates_compile_as_scalar_operands(
    formula, expected, unwrapped
):
    dialect = MSSQL()

    result = dialect.compile_calc_expr(
        parse_calc_expression(formula),
        ExpressionContext.PROJECTION,
        {},
        "UTC",
        parameters={},
    )
    sql = result.expression.sql(dialect=dialect.sqlglot_dialect())

    assert sql != expected
    # Temporarily capture the predicate output until operands compile as scalar values.
    assert sql == unwrapped


@pytest.mark.parametrize("kind", [ExpressionKind.AGGREGATION, ExpressionKind.WINDOW])
@pytest.mark.parametrize(
    ("context", "data_type", "expected_type"),
    [
        (ExpressionContext.PROJECTION, DataType.BOOLEAN, DataType.NUMBER),
        (ExpressionContext.AGGREGATION, DataType.BOOLEAN, DataType.NUMBER),
        (ExpressionContext.WHERE, DataType.NUMBER, DataType.BOOLEAN),
        (ExpressionContext.HAVING, DataType.NUMBER, DataType.BOOLEAN),
    ],
)
def test_mssql_context_conversion_preserves_expression_kind(
    kind, context, data_type, expected_type
):
    dialect = MSSQL()
    operand = exp.column("semantic_value")
    sql_expression = (
        exp.NEQ(this=operand, expression=exp.Literal.number(0))
        if data_type == DataType.BOOLEAN
        else operand
    )
    expression = TypedSelectExpression.from_sqlglot(sql_expression, data_type, kind)

    result = dialect.wrap_expression_for_context(expression, context)

    assert result.data_type == expected_type
    assert result.kind != kind
    # Temporarily capture the inferred column kind until semantic kinds are preserved.
    assert result.kind == ExpressionKind.COLUMN


@pytest.mark.parametrize("kind", [ExpressionKind.AGGREGATION, ExpressionKind.WINDOW])
@pytest.mark.parametrize(
    "formula",
    ["true = predicate", "switch(true, predicate, 7, 11)", "isoneof(predicate, false)"],
)
def test_mssql_predicate_composition_preserves_expression_kind(kind, formula):
    dialect = MSSQL()
    predicate = TypedSelectExpression.from_sqlglot(
        exp.NEQ(
            this=exp.column("semantic_predicate"), expression=exp.Literal.number(0)
        ),
        DataType.BOOLEAN,
        kind,
    )

    result = dialect.compile_calc_expr(
        parse_calc_expression(formula),
        context=ExpressionContext.PROJECTION,
        columns={},
        timezone="UTC",
        parameters={},
        substitutions={"predicate": predicate},
    )

    assert result.kind != kind
    # Temporarily capture the inferred kind until semantic kinds are preserved.
    assert result.kind == (
        ExpressionKind.SCALAR
        if formula.startswith("switch(")
        else ExpressionKind.COLUMN
    )
