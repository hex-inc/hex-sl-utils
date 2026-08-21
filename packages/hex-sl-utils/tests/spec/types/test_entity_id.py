from hex_sl_utils.spec.types import Model


def test_entity_id_schema_includes_description() -> None:
    schema = Model.model_json_schema()

    assert schema["$defs"]["EntityId"]["description"].startswith(
        "All IDs must conform to the following rules:"
    )
