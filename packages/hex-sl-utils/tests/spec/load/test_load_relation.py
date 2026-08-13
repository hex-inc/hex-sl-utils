from typing import Any

from inline_snapshot import snapshot

from hex_sl_utils.spec.load import load_project
from hex_sl_utils.spec.types import Relation

from .utils import make_yml, snapshot_yml_load_problems, tmp_project_dir

OK_MODEL_JSON = {"id": "test_model", "base_sql_table": "test"}
OK_RELATION_JSON = {
    "id": "test_relation",
    "type": "many_to_one",
    "join_sql": "${id} = ${test_relation.id}",
}


def make_model_relation_yml(**kwargs: Any) -> str:
    return make_yml(
        {
            **OK_MODEL_JSON,
            "dimensions": [{"id": "id", "type": "string"}],
            "relations": [{**OK_RELATION_JSON, **kwargs}],
        }
    )


def load_yml_model_relation(model_yml: str) -> Relation:
    target_model_yml = make_yml(
        {
            "id": "test_relation",
            "base_sql_table": "test",
            "dimensions": [{"id": "id", "type": "string"}],
        }
    )
    with tmp_project_dir(model_yml, target_model_yml) as project_dir:
        loaded = load_project(
            project_dir=project_dir,
            project_name="Test",
            dialect_name="duckdb",
        )
        assert loaded.problems == []
        return loaded.project.models[0].relations[0]


# ====== Basic load ======


def test_load_relation_ok():
    yml = make_model_relation_yml()
    ds = load_yml_model_relation(yml)
    assert ds.id == "test_relation"
    assert ds.target == "test_relation"  # inferred from id
    assert ds.type == "many_to_one"
    assert ds.join_sql == "${id} = ${test_relation.id}"


def test_load_relation_ok_target():
    yml = make_model_relation_yml(id="distinct_id", target="distinct_target")
    ds = load_yml_model_relation(yml)
    assert ds.id == "distinct_id"
    assert ds.target == "distinct_target"


# ====== Problem detection ======


def test_load_invalid_relation_missing_id():
    relation_json = {**OK_RELATION_JSON}
    del relation_json["id"]
    yml = make_yml({**OK_MODEL_JSON, "relations": [relation_json]})
    assert snapshot_yml_load_problems(yml) == snapshot(
        "[ERROR] Relation without an id or name: Field required at `id`"
    )


def test_load_invalid_relation_missing_type():
    relation_json = {**OK_RELATION_JSON}
    del relation_json["type"]
    yml = make_yml({**OK_MODEL_JSON, "relations": [relation_json]})
    assert snapshot_yml_load_problems(yml) == snapshot(
        "[ERROR] Relation `test_relation`: Field required at `type`"
    )


def test_load_invalid_relation_bad_type():
    yml = make_model_relation_yml(type="bad_type")
    assert snapshot_yml_load_problems(yml) == snapshot(
        "[ERROR] Relation `test_relation`: Input should be 'many_to_one', 'one_to_one' or 'one_to_many' at `type`"
    )


def test_load_invalid_relation_extra_key():
    yml = make_model_relation_yml(extra_key="extra_value")
    assert snapshot_yml_load_problems(yml) == snapshot(
        "[ERROR] Relation `test_relation`: Extra inputs are not permitted at `extra_key`"
    )
