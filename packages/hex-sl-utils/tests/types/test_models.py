import pytest
from pydantic import ValidationError

from hex_sl_utils.types import Dimension, Model, Project, Relation, View


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


def test_project_resource_discrimination() -> None:
    project = Project.model_validate(
        {
            "name": "Commerce",
            "dialect": "duckdb",
            "resources": [
                {"id": "orders", "base_sql_table": "analytics.orders"},
                {
                    "id": "order_view",
                    "type": "view",
                    "base": "orders",
                    "contents": [{"dimensions": "..."}],
                },
            ],
        }
    )

    assert isinstance(project.models[0], Model)
    assert isinstance(project.views[0], View)


def test_relation_target_defaults_to_id() -> None:
    relation = Relation.model_validate(
        {
            "id": "customers",
            "type": "many_to_one",
            "join_sql": "${customer_id} = ${customers.id}",
        }
    )

    assert relation.target == "customers"


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
