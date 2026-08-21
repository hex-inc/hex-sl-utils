from hex_sl_utils.spec.types import Model


def test_model_defaults() -> None:
    model = Model.model_validate(
        {
            "id": "order_items",
            "base_sql_table": "analytics.order_items",
            "dimensions": [{"id": "order_id", "type": "string"}],
        }
    )

    assert model.name == "Order items"
    assert model.dimensions[0].expr_sql == "order_id"
