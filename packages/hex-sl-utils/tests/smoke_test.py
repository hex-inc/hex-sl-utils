"""Smoke test for installed hex-sl-utils distributions."""

from pathlib import Path
from tempfile import TemporaryDirectory

import hex_sl_utils
from hex_sl_utils.load import load_project
from hex_sl_utils.types import Model

assert Path(hex_sl_utils.__file__).name == "__init__.py"

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
