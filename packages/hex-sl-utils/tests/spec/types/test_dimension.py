import pytest
from pydantic import ValidationError

from hex_sl_utils.spec.types import Dimension


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
