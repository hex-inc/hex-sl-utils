"""Access generated schemas distributed with :mod:`hex_sl_utils`."""

from __future__ import annotations

import json
from importlib.resources import files
from typing import Any


def resource_json_schema() -> dict[str, Any]:
    """Return the JSON Schema for a Hex semantic-layer resource."""
    schema = (
        files("hex_sl_utils")
        / "schema_files"
        / "jsonschema"
        / "hex_resource_schema.json"
    )
    return json.loads(schema.read_text(encoding="utf-8"))


def resource_typescript_declarations() -> str:
    """Return TypeScript declarations for Hex semantic-layer resources."""
    declarations = (
        files("hex_sl_utils") / "schema_files" / "ts" / "hex_resource_schema.d.ts"
    )
    return declarations.read_text(encoding="utf-8")
