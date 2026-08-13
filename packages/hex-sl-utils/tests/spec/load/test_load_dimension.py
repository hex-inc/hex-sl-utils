from typing import Any

from inline_snapshot import snapshot

from hex_sl_utils.spec.load import load_project
from hex_sl_utils.spec.types import Dimension

from .utils import make_yml, snapshot_yml_load_problems, tmp_project_dir

OK_MODEL_JSON = {"id": "test_model", "base_sql_table": "test"}
OK_DIMENSION_JSON = {"id": "test", "type": "string"}


def make_model_dimension_yml(**kwargs: Any) -> str:
    return make_yml(
        {
            **OK_MODEL_JSON,
            "dimensions": [{**OK_DIMENSION_JSON, **kwargs}],
        }
    )


def load_yml_model_dimension(model_yml: str) -> Dimension:
    with tmp_project_dir(model_yml) as project_dir:
        loaded = load_project(
            project_dir=project_dir,
            project_name="Test",
            dialect_name="duckdb",
        )
        assert loaded.problems == []
        return loaded.project.models[0].dimensions[0]


# ====== Basic load ======


def test_load_dimension_ok():
    yml = make_model_dimension_yml()
    ds = load_yml_model_dimension(yml)
    assert ds.id == "test"
    assert ds.type == "string"


def test_load_dimension_inferred_expr():
    yml = make_model_dimension_yml(id="my_column")
    ds = load_yml_model_dimension(yml)
    assert ds.id == "my_column"
    assert ds.expr_sql == "my_column"
    assert ds.expr_calc is None


def test_load_dimension_inferred_name():
    yml = make_model_dimension_yml(id="my_column")
    ds = load_yml_model_dimension(yml)
    assert ds.id == "my_column"
    assert ds.name == "My column"


# ====== Problem detection ======


def test_load_dimension_missing_id():
    dim_json = {**OK_DIMENSION_JSON}
    del dim_json["id"]
    yml = make_yml({**OK_MODEL_JSON, "dimensions": [dim_json]})
    assert snapshot_yml_load_problems(yml) == snapshot(
        "[ERROR] Dimension without an id or name: Field required at `id`"
    )


def test_load_dimension_missing_type():
    dim_json = {**OK_DIMENSION_JSON}
    del dim_json["type"]
    yml = make_yml({**OK_MODEL_JSON, "dimensions": [dim_json]})
    assert snapshot_yml_load_problems(yml) == snapshot(
        "[ERROR] Dimension `test`: Field required at `type`"
    )


def test_load_invalid_dimension_conflicting_expr():
    yml = make_model_dimension_yml(expr_sql="1", expr_calc="1")
    assert snapshot_yml_load_problems(yml) == snapshot(
        "[ERROR] Dimension `test`: Only one of `expr_sql` or `expr_calc` can be provided"
    )


def test_load_invalid_dimension_bad_type():
    yml = make_model_dimension_yml(type="bad_type")
    assert snapshot_yml_load_problems(yml) == snapshot(
        "[ERROR] Dimension `test`: Input should be 'number', 'string', 'timestamp_tz', 'timestamp_naive', 'date', 'boolean', 'null' or 'other' at `type`"
    )


def test_load_invalid_dimension_extra_key():
    yml = make_model_dimension_yml(extra_key="extra_value")
    assert snapshot_yml_load_problems(yml) == snapshot(
        "[ERROR] Dimension `test`: Extra inputs are not permitted at `extra_key`"
    )
