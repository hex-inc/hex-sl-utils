from hex_sl_utils.spec.types import Model, Project, View


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
