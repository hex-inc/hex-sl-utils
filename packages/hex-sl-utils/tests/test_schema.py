from hex_sl_utils.schema import (
    resource_json_schema,
    resource_typescript_declarations,
)


def test_resource_json_schema_is_distributed() -> None:
    schema = resource_json_schema()

    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["title"] == "Resource"


def test_resource_typescript_declarations_are_distributed() -> None:
    declarations = resource_typescript_declarations()

    assert "export type Resource =" in declarations
