from typing import Any

from inline_snapshot import snapshot

from hex_sl_utils.load import load_project
from hex_sl_utils.types import View

from .utils import (
    make_stub_model,
    make_yml,
    snapshot_yml_load_problems,
    tmp_project_dir,
)

OK_VIEW_JSON = {
    "id": "test",
    "type": "view",
    "base": "test_model",
    "contents": [{"dimensions": "...", "measures": "..."}],
}


def make_view_yml(**kwargs: Any) -> str:
    return make_yml({**OK_VIEW_JSON, **kwargs})


def load_yml_view(yml: str, *peer_ymls: str) -> View:
    with tmp_project_dir(
        yml,
        *peer_ymls,
        make_stub_model("test_model"),
    ) as project_dir:
        loaded = load_project(
            project_dir=project_dir,
            project_name="Test",
            dialect_name="duckdb",
        )
        assert loaded.problems == [], loaded.problems
        return loaded.project.views[0]


# ====== Basic load ======


def test_load_view_ok():
    yml = make_view_yml()
    view = load_yml_view(yml)
    assert view.id == "test"
    assert len(view.contents) == 1
    assert view.contents[0].dimensions == "..."
    assert view.contents[0].measures == "..."


# ====== Problem detection ======


def test_load_invalid_yml():
    yml = """\
    id: test
    oh no
    type: view
    base: test_model
    contents:
        - dimensions: *
          measures: *
    """
    assert snapshot_yml_load_problems(yml) == snapshot(
        """\
[ERROR] Invalid YAML in file `file_0.yml`: 2:10: (22B): ERROR: could not find ':' colon after key
2:10:     oh no  (size=9)
               ^  (cols 10-10)\
"""
    )


def test_load_invalid_view_missing_fields():
    yml = make_yml({"id": "test", "type": "view"})
    assert snapshot_yml_load_problems(yml) == snapshot(
        """\
[ERROR] View `test`: Field required at `base`

[ERROR] View `test`: Field required at `contents`\
"""
    )


def test_load_view_recovers_missing_fields():
    yml = make_yml({"id": "test", "type": "view"})
    with tmp_project_dir(yml, make_stub_model("test_model")) as project_dir:
        loaded = load_project(
            project_dir=project_dir,
            project_name="Test",
            dialect_name="duckdb",
        )

    assert len(loaded.project.views) == 1
    assert loaded.project.views[0].base == ""
    assert loaded.project.views[0].contents == []


def test_load_view_extra_key():
    yml = make_view_yml(extra_key="extra_value")
    assert snapshot_yml_load_problems(yml) == snapshot(
        "[ERROR] View `test`: Extra inputs are not permitted at `extra_key`"
    )


def test_load_view_bad_id():
    yml = make_view_yml(id="bad id")
    assert snapshot_yml_load_problems(yml) == snapshot(
        "[ERROR] View `bad id`: String should match pattern '^[a-z_][a-z0-9_]{1,127}$' at `id`"
    )


def test_load_view_bad_short_id():
    yml = make_view_yml(id="i")
    assert snapshot_yml_load_problems(yml) == snapshot(
        "[ERROR] View `i`: String should have at least 2 characters at `id`"
    )


def test_load_view_bad_reserved_id():
    yml = make_view_yml(id="model")
    assert snapshot_yml_load_problems(yml) == snapshot(
        "[ERROR] View `model`: ID 'model' is a reserved term and cannot be used at `id`"
    )


def test_load_view_bad_reserved_id_prefix():
    yml = make_view_yml(id="__hex_test")
    assert snapshot_yml_load_problems(yml) == snapshot(
        "[ERROR] View `__hex_test`: ID '__hex_test' cannot begin with '__hex' at `id`"
    )


def test_load_view_bad_id_number_start():
    yml = make_view_yml(id="5test")
    assert snapshot_yml_load_problems(yml) == snapshot(
        "[ERROR] View `5test`: String should match pattern '^[a-z_][a-z0-9_]{1,127}$' at `id`"
    )


def test_load_view_bad_id_too_long():
    chars = "a" * 128
    yml = make_view_yml(id=f"test_{chars}")
    assert snapshot_yml_load_problems(yml) == snapshot(
        "[ERROR] View `test_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`: String should have at most 128 characters at `id`"
    )
