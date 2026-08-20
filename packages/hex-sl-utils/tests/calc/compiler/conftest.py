import pytest

from hex_sl_utils.calc.compiler import CalcToTypedSelectVisitor
from hex_sl_utils.dialect.clickhouse import ClickHouse
from hex_sl_utils.expr import ExpressionContext


@pytest.fixture
def visitor() -> CalcToTypedSelectVisitor:
    columns = {}
    return CalcToTypedSelectVisitor(
        ClickHouse(),
        ExpressionContext.PROJECTION,
        columns,
        timezone="America/New_York",
    )
