from __future__ import annotations

import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel

from hex_sl_utils.load import load_project
from hex_sl_utils.types import Model, Problem, Resource

here = Path(__file__).parent


class _Dumper(yaml.SafeDumper):
    pass


def _represent_string(dumper: yaml.SafeDumper, value: str) -> yaml.ScalarNode:
    style = '"' if "\n" in value else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", value, style=style)


_Dumper.add_representer(str, _represent_string)


@contextmanager
def tmp_project_dir(*documents: str | Resource) -> Iterator[Path]:
    with tempfile.TemporaryDirectory() as temp_dir:
        project_dir = Path(temp_dir)
        for index, document in enumerate(documents):
            text = (
                document
                if isinstance(document, str)
                else make_yml(document.model_dump(mode="json"))
            )
            (project_dir / f"file_{index}.yml").write_text(text)
        yield project_dir


def get_test_project_dir(project_name: str) -> Path:
    path = here / "projects" / project_name
    assert path.exists(), f"Project {project_name} not found"
    return path


def make_stub_model(model_id: str = "test") -> Model:
    return Model.model_construct(
        id=model_id,
        type="model",
        base_sql_table="test_table",
    )


def make_yml(value: Any) -> str:
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json", exclude_none=True)
    return yaml.dump(value, Dumper=_Dumper, sort_keys=False)


def problems_snapshot(
    problems: list[Problem],
    *,
    include_causes: bool = False,
    include_impacts: bool = False,
) -> str:
    return "\n\n".join(
        problem.to_str(
            include_causes=include_causes,
            include_impacts=include_impacts,
        )
        for problem in problems
    )


def snapshot_yml_load_problems(
    yml: str,
    *,
    include_causes: bool = False,
    include_impacts: bool = False,
) -> str:
    ok_yml = make_yml({"id": "injected_ok_model", "base_sql_table": "test"})
    with tmp_project_dir(yml, ok_yml) as project_dir:
        loaded = load_project(
            project_dir=project_dir,
            project_name="Test",
            dialect_name="duckdb",
        )
    return problems_snapshot(
        loaded.problems,
        include_causes=include_causes,
        include_impacts=include_impacts,
    )
