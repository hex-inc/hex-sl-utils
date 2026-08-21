import pytest
from pydantic import ValidationError
from typing_extensions import assert_type

from hex_sl_utils.spec.types import DataType, Dimension


def test_dimension_without_optional_fields() -> None:
    # should not fail pyright type checking
    dimension = Dimension(id="order_id", type=DataType.STRING)
    assert_type(dimension, Dimension)


def test_dimension_rejects_conflicting_expressions() -> None:
    with pytest.raises(ValidationError, match="Only one of"):
        Dimension.model_validate(
            {
                "id": "order_id",
                "type": "string",
                "expr_sql": "order_id",
                "expr_calc": "order_id",
            }
        )
