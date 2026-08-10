from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

from pydantic import RootModel
from pydantic.json_schema import GenerateJsonSchema, JsonSchemaValue
from pydantic_core import CoreSchema

from hex_sl_utils.types import Resource

here = Path(__file__).absolute().parent
root = here.parent.parent


class HexResourceRoot(RootModel[Resource]):
    model_config = {
        "json_schema_extra": {
            "title": "HexResource",
            "description": "Union over all definable resource types",
        }
    }


class TitleGenerateJsonSchema(GenerateJsonSchema):
    """
    Custom JSON schema generator that updates the $defs in the schema to
    match their title rather than Python class name.
    """

    def generate(self, schema: CoreSchema, mode: str = "validation") -> JsonSchemaValue:
        json_schema = super().generate(schema, mode=mode)  # pyright: ignore[reportArgumentType]
        for key, item in list(json_schema.get("$defs", {}).items()):
            title = item.get("title")
            title = title and self._transform_key(title)
            if title and title != key:
                json_schema["$defs"][key]["title"] = title
                json_schema["$defs"][title] = json_schema["$defs"].pop(key)
                self._update_refs(json_schema, key, title)
        if json_schema.get("title"):
            json_schema["title"] = self._transform_key(json_schema["title"])
        return json_schema

    def _transform_key(self, key: str) -> str:
        return key

    def _update_refs(
        self,
        schema: dict[str, CoreSchema] | list[CoreSchema],
        old_name: str,
        new_name: str,
    ) -> None:
        if isinstance(schema, dict):
            for key, value in schema.items():
                if key == "$ref" and value == f"#/$defs/{old_name}":
                    schema[key] = f"#/$defs/{new_name}"  # pyright: ignore[reportArgumentType]
                elif isinstance(value, (dict, list)):
                    self._update_refs(value, old_name, new_name)  # pyright: ignore[reportArgumentType]
        elif isinstance(schema, list):
            for item in schema:
                self._update_refs(item, old_name, new_name)  # pyright: ignore[reportArgumentType]


class HexGenerateJsonSchema(TitleGenerateJsonSchema):
    """Remove `Hex` prefixes from definition names in a schema."""

    def _transform_key(self, key: str) -> str:
        if key.startswith("Hex"):
            return key[len("Hex") :]
        return key


def export_json_schemas() -> None:
    """Export the JSON Schema and TypeScript declarations for Hex resources."""
    schema_dir = (
        root
        / "packages"
        / "hex-sl-utils"
        / "src"
        / "hex_sl_utils"
        / "schema_files"
        / "jsonschema"
    )
    if schema_dir.exists():
        shutil.rmtree(schema_dir)
    schema_dir.mkdir(parents=True, exist_ok=True)

    schema = HexResourceRoot.model_json_schema(
        schema_generator=HexGenerateJsonSchema,
    )
    with schema_dir.joinpath("hex_resource_schema.json").open("w") as file:
        json.dump(schema, file, indent=2)

    ts_dir = schema_dir.parent / "ts"
    if ts_dir.exists():
        shutil.rmtree(ts_dir)
    ts_dir.mkdir(parents=True, exist_ok=True)

    subprocess.run(["pnpm", "install", "--frozen-lockfile"], check=True, cwd=root)
    subprocess.run(
        ["pnpm", "--filter", "@hex/sl-utils-scripts-schema", "run", "build"],
        check=True,
        cwd=root,
    )

    print("Validating generated TypeScript files...")
    for ts_file in ts_dir.glob("*.d.ts"):
        print(f"  Checking {ts_file.name}...")
        content = ts_file.read_text()
        self_ref_pattern = r"export\s+type\s+(\w+)\s*=\s*.*\b\1\b.*?;"

        for line_num, line in enumerate(content.split("\n"), 1):
            match = re.search(self_ref_pattern, line)
            if match:
                type_name = match.group(1)
                msg = f"Self-referential type '{type_name}' in {ts_file.name}"
                raise RuntimeError(msg)

        print(f"    ✓ {ts_file.name} - no self-referential types found")


if __name__ == "__main__":
    export_json_schemas()
