from typing import Any, cast

from inline_snapshot import snapshot

from hex_sl_utils.load import load_project

from .utils import (
    get_test_project_dir,
    make_stub_model,
    make_yml,
    problems_snapshot,
    tmp_project_dir,
)

# ====== Problem detection ======


def test_load_invalid_dialect():
    loaded = load_project(
        project_dir=get_test_project_dir("slim_ok"),
        project_name="",
        dialect_name=cast(Any, "invalid_dialect"),
    )
    assert problems_snapshot(loaded.problems) == snapshot(
        "[FATAL] Invalid dialect name: invalid_dialect"
    )


def test_load_no_models():
    with tmp_project_dir() as project_dir:
        loaded = load_project(
            project_dir=project_dir,
            project_name="",
            dialect_name="duckdb",
        )
    assert problems_snapshot(loaded.problems) == snapshot(
        "[ERROR] No valid models found."
    )


def test_source_info():
    loaded = load_project(
        project_dir=get_test_project_dir("slim_ok"),
        project_name="",
        dialect_name="duckdb",
    )
    assert len(loaded.source_files) == 2

    model_file = loaded.source_files[0]
    assert model_file.filepath.endswith("model.yml")
    assert model_file.contents_text.strip().startswith("id: test_model")
    model_file_resources = model_file.resources
    assert len(model_file_resources) == 1
    assert model_file_resources[0].resource_id == "test_model"
    assert model_file_resources[0].resource_type == "model"

    view_file = loaded.source_files[1]
    assert view_file.filepath.endswith("view.yml")
    assert view_file.contents_text.strip().startswith("id: test_view")
    view_file_resources = view_file.resources
    assert len(view_file_resources) == 1
    assert view_file_resources[0].resource_id == "test_view"
    assert view_file_resources[0].resource_type == "view"


def test_load_utf8_source_file():
    yml = make_yml(
        {
            "id": "international_model",
            "base_sql_table": "international_table",
            "description": "Crème brûlée 🍮",
        }
    )
    with tmp_project_dir(yml) as project_dir:
        loaded = load_project(
            project_dir=project_dir,
            project_name="Test",
            dialect_name="duckdb",
        )

    assert loaded.problems == []
    assert loaded.project.models[0].description == "Crème brûlée 🍮"


def test_load_multiple_resources_in_file():
    d1 = make_yml(make_stub_model("model_1").model_dump(mode="json"))
    d2 = make_yml(make_stub_model("model_2").model_dump(mode="json"))
    d1_d2_combined = f"{d1}---\n{d2}"
    d3_separate = make_yml(make_stub_model("model_3").model_dump(mode="json"))

    with tmp_project_dir(d1_d2_combined, d3_separate) as project_dir:
        result = load_project(
            project_dir=project_dir,
            project_name="",
            dialect_name="duckdb",
        )
        source_files = result.source_files
        models = result.project.models
        assert result.problems == []

    assert len(source_files) == 2
    assert len(models) == 3

    assert models[0].id == "model_1"
    assert models[1].id == "model_2"
    assert models[2].id == "model_3"

    # the first file contains both `d1` and `d2`
    d1_d2_file = source_files[0]
    assert d1_d2_file.contents_text == d1_d2_combined

    assert len(d1_d2_file.resources) == 2
    assert d1_d2_file.resources[0].resource_id == "model_1"
    assert d1_d2_file.resources[0].resource_type == "model"
    assert d1_d2_file.resources[1].resource_id == "model_2"
    assert d1_d2_file.resources[1].resource_type == "model"

    # the second file only contains `d3`
    d3_file = source_files[1]
    assert d3_file.contents_text == d3_separate

    assert len(d3_file.resources) == 1
    assert d3_file.resources[0].resource_id == "model_3"
    assert d3_file.resources[0].resource_type == "model"

    # ensure separate files
    assert d3_file.filepath != d1_d2_file.filepath


def test_load_invalid_file_info():
    bad_yml = "["
    ok_yml_no_resource = "hello: world"
    ok_yml_with_resource = make_yml(make_stub_model("model_1").model_dump(mode="json"))

    with tmp_project_dir(
        bad_yml,
        ok_yml_no_resource,
        ok_yml_with_resource,
    ) as project_dir:
        result = load_project(
            project_dir=project_dir,
            project_name="",
            dialect_name="duckdb",
        )
        source_files = result.source_files
        models = result.project.models
        assert len(result.problems) >= 2

    assert len(source_files) == 3
    assert len(models) == 1

    assert models[0].id == "model_1"

    bad_yml_file = source_files[0]
    assert bad_yml_file.contents_text == bad_yml
    assert len(bad_yml_file.resources) == 0

    ok_yml_no_resource_file = source_files[1]
    assert ok_yml_no_resource_file.contents_text == ok_yml_no_resource
    assert len(ok_yml_no_resource_file.resources) == 1
    assert ok_yml_no_resource_file.resources[0].resource_id is None
    assert ok_yml_no_resource_file.resources[0].resource_type == "unknown"

    ok_yml_with_resource_file = source_files[2]
    assert ok_yml_with_resource_file.resources[0].resource_id == "model_1"
    assert ok_yml_with_resource_file.resources[0].resource_type == "model"
