import pytest
from hex_sl.calc.compiler import CalcToTypedSelectVisitor
from hex_sl.dialect.clickhouse import HexSLClickHouse
from hex_sl.expr import ExpressionContext
from hex_sl.schema import Schema


@pytest.fixture
def visitor() -> CalcToTypedSelectVisitor:
    schema = Schema(name="test_schema", types={})
    return CalcToTypedSelectVisitor(
        HexSLClickHouse(),
        ExpressionContext.PROJECTION,
        schema,
        timezone="America/New_York",
    )
