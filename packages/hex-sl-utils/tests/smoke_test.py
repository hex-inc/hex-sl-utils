"""Smoke test for installed hex-sl-utils distributions."""

from pathlib import Path
from tempfile import TemporaryDirectory

import hex_sl_utils
from hex_sl_utils.dialect import Dialect
from hex_sl_utils.expr import QualifiedReference, get_placeholder_references
from hex_sl_utils.schema import (
    resource_json_schema,
    resource_typescript_declarations,
)
from hex_sl_utils.spec.load import load_project
from hex_sl_utils.spec.types import Model

assert Path(hex_sl_utils.__file__).name == "__init__.py"
assert resource_json_schema()["title"] == "Resource"
assert "export type Resource =" in resource_typescript_declarations()

with TemporaryDirectory() as temp_dir:
    project_dir = Path(temp_dir)
    (project_dir / "model.yml").write_text(
        "id: smoke_test\nbase_sql_table: smoke_test\n",
        encoding="utf-8",
    )
    loaded = load_project(
        project_dir=project_dir,
        project_name="Smoke test",
        dialect_name="duckdb",
    )

assert loaded.problems == []
assert len(loaded.project.models) == 1
assert isinstance(loaded.project.models[0], Model)
assert loaded.project.models[0].id == "smoke_test"

references = get_placeholder_references(
    "${amount} + ${ABC.tax} + ${buyer.name}",
    resource="orders",
    dialect=Dialect.from_name("duckdb"),
    marker="ABC",
)
assert set(references) == {
    ("orders", "amount"),
    ("orders", "tax"),
    ("buyer", "name"),
}
qualified_reference: QualifiedReference = (("buyer",), "name")
assert qualified_reference == (("buyer",), "name")
