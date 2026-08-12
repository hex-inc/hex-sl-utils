from inline_snapshot import snapshot

from hex_sl_utils._vendor.sqlglot import exp, parse_one
from hex_sl_utils.calc.ast.expr import CalcExpr
from hex_sl_utils.calc.ast.sql_expression import SqlExpression
from hex_sl_utils.calc.compiled import ExpressionContext
from hex_sl_utils.calc.compiler import CalcToTypedSelectVisitor
from hex_sl_utils.calc.parser import parse_calc_expression
from hex_sl_utils.calc.substitution import ColumnSubstitutionVisitor
from hex_sl_utils.calc.visitor import HEXSL_CALC_FN_NAME
from hex_sl_utils.types import DataType

from ._dialect import TestDialect


def test_sql_expression_with_hexsl_calc_substitution():
    # Create a SqlExpression with a column reference
    sql_expr = SqlExpression(sql="amount * tax_rate", data_type=DataType.NUMBER)

    # Create substitutions
    substitutions = {"tax_rate": parse_calc_expression("0.08 + regional_rate").root}

    # Apply substitution with dialect
    dialect = TestDialect()
    visitor = ColumnSubstitutionVisitor(substitutions, dialect)
    result = sql_expr.accept(visitor)

    # Check that the SQL contains _hexsl_calc placeholder with JSON
    assert result.sql == snapshot(
        'amount * _HEXSL_CALC(\'{"lhs":{"number":0.08},"rhs":{"name":"regional_rate","qualifiers":[]},"binary":"+"}\')'
    )

    # Parse and verify the structure
    sqlglot_expr = parse_one(result.sql, dialect=dialect.sqlglot_dialect())
    calc_json = None
    for node in sqlglot_expr.walk():
        if isinstance(node, exp.Anonymous) and node.this.upper() == HEXSL_CALC_FN_NAME:
            calc_json = node.expressions[0].this

    # Verify we can parse the JSON back to a CalcExpr
    calc_expr = CalcExpr.model_validate_json(calc_json)
    # Should be the substituted expression
    assert calc_expr.to_string() == "(0.08 + regional_rate)"


def test_column_extraction_from_hexsl_calc():
    # Create SqlExpression with _hexsl_calc placeholder containing JSON
    calc_json = parse_calc_expression("price + tax").model_dump_json(by_alias=True)
    sql_with_placeholder = f"amount * _hexsl_calc('{calc_json}')"
    sql_expr = SqlExpression(sql=sql_with_placeholder, data_type=DataType.NUMBER)

    from ._dialect import TestDialect

    dialect = TestDialect()

    calc_expr = CalcExpr(root=sql_expr)
    columns = calc_expr.get_unqualified_columns(dialect)

    # Should extract 'amount' from SQL and 'price', 'tax' from the calc
    assert set(columns) == {"amount", "price", "tax"}


def test_full_compilation_with_resolution():
    # Create SqlExpression with placeholder containing JSON
    calc_json = parse_calc_expression("1 + 2").model_dump_json(by_alias=True)
    sql_expr = SqlExpression(
        sql=f"amount * _hexsl_calc('{calc_json}')", data_type=DataType.NUMBER
    )

    # Set up compilation context
    dialect = TestDialect()
    schema = {"amount": DataType.NUMBER}

    # Compile with resolution
    compiler = CalcToTypedSelectVisitor(
        dialect=dialect,
        context=ExpressionContext.PROJECTION,
        schema=schema,
        timezone="UTC",
        skip_mangle=True,  # Skip mangling for this test
    )

    typed_expr = sql_expr.accept(compiler)

    # The placeholder should be resolved to actual SQL
    sql_output = typed_expr.expression.sql(dialect=dialect.sqlglot_dialect())
    assert sql_output == '"amount" * (1 + 2)'


def test_recursive_hexsl_calc_substitution():
    # Test that existing _hexsl_calc placeholders have substitutions applied
    calc_json = parse_calc_expression("price + tax_rate").model_dump_json(by_alias=True)
    sql_expr = SqlExpression(
        sql=f"amount * _hexsl_calc('{calc_json}')", data_type=DataType.NUMBER
    )

    # Create substitutions that affect the calc inside the placeholder
    substitutions = {"tax_rate": parse_calc_expression("0.08").root}

    # Apply substitution with dialect
    dialect = TestDialect()
    visitor = ColumnSubstitutionVisitor(substitutions, dialect)
    result = sql_expr.accept(visitor)

    # Check that the SQL still contains _hexsl_calc placeholder with JSON
    assert result.sql == snapshot(
        'amount * _HEXSL_CALC(\'{"lhs":{"name":"price","qualifiers":[]},"rhs":{"number":0.08},"binary":"+"}\')'
    )

    # Parse and verify the placeholder was updated
    sqlglot_expr = parse_one(result.sql, dialect=dialect.sqlglot_dialect())
    calc_json_updated = None
    for node in sqlglot_expr.walk():
        if isinstance(node, exp.Anonymous) and node.this.upper() == HEXSL_CALC_FN_NAME:
            # The calc expression should now have the substituted value
            calc_json_updated = node.expressions[0].this

    # Parse JSON and verify substitution happened
    calc_expr = CalcExpr.model_validate_json(calc_json_updated)
    assert calc_expr.to_string() == "(price + 0.08)"


def test_sql_expression_basic():
    # Test basic SqlExpression creation
    sql_expr = SqlExpression(
        sql="CASE WHEN score > 90 THEN 'A' ELSE 'B' END", data_type=DataType.STRING
    )

    # Test that it can be wrapped in CalcExpr
    calc_expr = CalcExpr(root=sql_expr)

    # Test string representation
    str_repr = calc_expr.to_string()
    assert str_repr == "SQL(CASE WHEN score > 90 THEN 'A' ELSE 'B' END)"


def test_sql_expression_no_substitutions():
    # Test SqlExpression with no substitutions needed
    sql_expr = SqlExpression(sql="10 * 20", data_type=DataType.NUMBER)

    dialect = TestDialect()
    visitor = ColumnSubstitutionVisitor({}, dialect)
    result = sql_expr.accept(visitor)

    # Should return the same SqlExpression unchanged
    assert result.sql == sql_expr.sql
    assert result.data_type == sql_expr.data_type


def test_sql_expression_with_multiple_columns():
    # Test substitution of multiple columns
    sql_expr = SqlExpression(sql="col1 + col2 * col3", data_type=DataType.NUMBER)

    substitutions = {
        "col1": parse_calc_expression("10").root,
        "col2": parse_calc_expression("20").root,
        "col3": parse_calc_expression("price + tax").root,
    }

    dialect = TestDialect()
    visitor = ColumnSubstitutionVisitor(substitutions, dialect)
    result = sql_expr.accept(visitor)

    # Should have three _hexsl_calc placeholders (case-insensitive)
    calc_count = result.sql.upper().count(HEXSL_CALC_FN_NAME)
    assert calc_count == 3


def test_sql_expression_with_aggregate_detection():
    # Test that aggregate functions in SQL are detected
    sql_expr = SqlExpression(sql="SUM(amount) / COUNT(*)", data_type=DataType.NUMBER)

    from ._dialect import TestDialect

    dialect = TestDialect()

    calc_expr = CalcExpr(root=sql_expr)
    has_agg = calc_expr.has_aggregation(dialect)
    assert has_agg is True


def test_sql_expression_with_aggregate_in_placeholder():
    # Test that aggregate functions in placeholders are detected
    calc_json = parse_calc_expression("sum(price)").model_dump_json(by_alias=True)
    sql_expr = SqlExpression(
        sql=f"amount * _hexsl_calc('{calc_json}')", data_type=DataType.NUMBER
    )

    from ._dialect import TestDialect

    dialect = TestDialect()

    calc_expr = CalcExpr(root=sql_expr)
    has_agg = calc_expr.has_aggregation(dialect)
    assert has_agg is True


def test_sql_expression_qualified_columns():
    # Test extraction of qualified column references
    sql_expr = SqlExpression(
        sql="orders.amount + customers.credit", data_type=DataType.NUMBER
    )

    from ._dialect import TestDialect

    dialect = TestDialect()

    calc_expr = CalcExpr(root=sql_expr)
    all_columns = calc_expr.get_all_columns(dialect)

    # Should have qualified references
    assert (("orders",), "amount") in all_columns
    assert (("customers",), "credit") in all_columns


def test_sql_expression_substituted_with_sql_expression():
    """Test substituting a column with a SqlExpression.

    This test verifies that SqlExpression nodes can be substituted into other
    SqlExpression nodes using JSON serialization in the placeholder.
    """

    # Create a SQL expression with a column reference
    sql_expr = SqlExpression(sql="price * multiplier", data_type=DataType.NUMBER)

    # Substitute multiplier with another SqlExpression
    substitutions = {
        "multiplier": SqlExpression(
            sql="CASE WHEN category = 'A' THEN 1.1 ELSE 1.0 END",
            data_type=DataType.NUMBER,
        )
    }

    dialect = TestDialect()
    calc = CalcExpr(root=sql_expr)

    # Substitution creates the placeholder with JSON
    substituted = calc.substitute(substitutions=substitutions, dialect=dialect)

    # The placeholder now contains JSON instead of unparsable 'SQL(...)'
    assert isinstance(substituted.root, SqlExpression)
    assert substituted.root.sql == snapshot(
        'price * _HEXSL_CALC(\'{"sql":"CASE WHEN category = \'\'A\'\' THEN 1.1 ELSE 1.0 END","data_type":"number"}\')'
    )

    # Now compile - this should succeed with JSON serialization
    schema = {
        "price": DataType.NUMBER,
        "category": DataType.STRING,
    }

    compiler = CalcToTypedSelectVisitor(
        dialect=dialect,
        context=ExpressionContext.PROJECTION,
        schema=schema,
        timezone="UTC",
        skip_mangle=True,
    )

    # Compilation should succeed
    typed_expr = substituted.root.accept(compiler)
    result_sql = typed_expr.expression.sql(dialect=dialect.sqlglot_dialect())

    # Verify the generated SQL
    assert result_sql == snapshot(
        '"price" * CASE WHEN "*category" = \'A\' THEN 1.1 ELSE 1.0 END'
    )
