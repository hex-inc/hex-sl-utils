from typing import assert_type

from hex_sl_utils.spec.types import DataType, ScalarExpression


def test_scalar_expression_without_optional_fields() -> None:
    # should not fail pyright type checking
    scalar_expression = ScalarExpression(
        id="order_id", type=DataType.STRING, expr_sql="order_id"
    )
    assert_type(scalar_expression, ScalarExpression)
