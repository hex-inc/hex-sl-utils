from typing import Any

from inline_snapshot import snapshot

from hex_sl_utils.load import load_project
from hex_sl_utils.types import Model

from .utils import make_yml, snapshot_yml_load_problems, tmp_project_dir

OK_MODEL_JSON = {"id": "test", "base_sql_table": "test"}


def make_model_yml(**kwargs: Any) -> str:
    return make_yml({**OK_MODEL_JSON, **kwargs})


def load_yml_model(yml: str, *peer_ymls: str) -> Model:
    with tmp_project_dir(yml, *peer_ymls) as project_dir:
        loaded = load_project(
            project_dir=project_dir,
            project_name="Test",
            dialect_name="duckdb",
        )
        assert loaded.problems == []
        return loaded.project.models[0]


# ====== Basic load ======


def test_load_model_ok():
    yml = make_model_yml()
    ds = load_yml_model(yml)
    assert ds.id == "test"
    assert ds.base_sql_table == "test"


def test_load_model_inferred_name():
    yml = make_model_yml(id="my_test_model")
    ds = load_yml_model(yml)
    assert ds.id == "my_test_model"
    assert ds.name == "My test model"


# ====== Problem detection ======


def test_load_invalid_yml():
    yml = """\
    id: test
    oh no
    base_sql_table: test
    """
    problems = snapshot_yml_load_problems(yml)
    assert problems.startswith("[ERROR] Invalid YAML in file `file_0.yml`:")
    assert "could not find ':'" in problems


def test_load_invalid_model_missing_base():
    yml = make_yml({"id": "test"})
    assert snapshot_yml_load_problems(yml) == snapshot(
        "[ERROR] Model `test`: Either `base_sql_query` or `base_sql_table` must be provided"
    )


def test_load_invalid_model_conflicting_base():
    yml = make_model_yml(
        base_sql_table="test",
        base_sql_query="SELECT * FROM test",
    )
    assert snapshot_yml_load_problems(yml, include_causes=True) == snapshot(
        """\
[ERROR] Model `test`: Only one of `base_sql_query` or `base_sql_table` can be provided
Cause: ['test', 'base_sql_query:'], ['test', 'base_sql_table:']\
"""
    )


def test_load_model_extra_key():
    yml = make_model_yml(extra_key="extra_value")
    assert snapshot_yml_load_problems(yml) == snapshot(
        "[ERROR] Model `test`: Extra inputs are not permitted at `extra_key`"
    )


def test_load_model_reports_non_list_members():
    yml = make_model_yml(dimensions={"id": "test_dimension", "type": "string"})
    assert snapshot_yml_load_problems(yml, include_causes=True) == snapshot(
        """\
[ERROR] Dimensions must be provided as a list
Cause: ['test', 'dimensions']\
"""
    )


def test_load_model_reports_non_mapping_member():
    yml = make_model_yml(dimensions=["test_dimension"])
    assert snapshot_yml_load_problems(yml, include_causes=True) == snapshot(
        """\
[ERROR] Dimension without an id or name: Input should be a valid dictionary or instance of Dimension
Cause: ['test', 'dimensions']\
"""
    )


def test_load_model_bad_id():
    yml = make_model_yml(id="bad id")
    assert snapshot_yml_load_problems(yml) == snapshot(
        "[ERROR] Model `bad id`: String should match pattern '^[a-z_][a-z0-9_]{1,127}$' at `id`"
    )


def test_load_model_bad_short_id():
    yml = make_model_yml(id="i")
    assert snapshot_yml_load_problems(yml) == snapshot(
        "[ERROR] Model `i`: String should have at least 2 characters at `id`"
    )


def test_load_model_bad_reserved_id():
    yml = make_model_yml(id="model")
    assert snapshot_yml_load_problems(yml) == snapshot(
        "[ERROR] Model `model`: ID 'model' is a reserved term and cannot be used at `id`"
    )


def test_load_model_bad_reserved_id_prefix():
    yml = make_model_yml(id="__hex_test")
    assert snapshot_yml_load_problems(yml) == snapshot(
        "[ERROR] Model `__hex_test`: ID '__hex_test' cannot begin with '__hex' at `id`"
    )


def test_load_model_bad_id_number_start():
    yml = make_model_yml(id="5test")
    assert snapshot_yml_load_problems(yml) == snapshot(
        "[ERROR] Model `5test`: String should match pattern '^[a-z_][a-z0-9_]{1,127}$' at `id`"
    )


def test_load_model_bad_id_too_long():
    chars = "a" * 128
    yml = make_model_yml(id=f"test_{chars}")
    assert snapshot_yml_load_problems(yml) == snapshot(
        "[ERROR] Model `test_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`: String should have at most 128 characters at `id`"
    )
