from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import pytest
from inline_snapshot import snapshot

from hex_sl_utils.spec.load import load_project, load_project_files

from .utils import (
    get_test_project_dir,
    make_stub_model,
    make_yml,
    problems_snapshot,
    tmp_project_dir,
)

# ====== Problem detection ======


def test_load_project_files_from_memory():
    model_1 = make_yml(make_stub_model("model_1").model_dump(mode="json"))
    model_2 = make_yml(make_stub_model("model_2").model_dump(mode="json"))

    loaded = load_project_files(
        files={"models.yml": f"{model_1}---\n{model_2}"},
        project_name="Demo",
        dialect_name="snowflake",
    )

    assert loaded.problems == []
    assert loaded.project.name == "Demo"
    assert loaded.project.dialect.root == "snowflake"
    assert [model.id for model in loaded.project.models] == ["model_1", "model_2"]
    assert loaded.source_files[0].filepath == "models.yml"
    assert loaded.source_files[0].contents_text == f"{model_1}---\n{model_2}"


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


def test_load_missing_project_directory(tmp_path: Path):
    missing_dir = tmp_path / "missing"
    loaded = load_project(
        project_dir=missing_dir,
        project_name="",
        dialect_name="duckdb",
    )
    assert problems_snapshot(loaded.problems) == snapshot(
        f"[FATAL] Project directory does not exist: `{missing_dir}`"
    )


def test_load_project_path_must_be_directory(tmp_path: Path):
    project_file = tmp_path / "project.yml"
    project_file.write_text("", encoding="utf-8")
    loaded = load_project(
        project_dir=project_file,
        project_name="",
        dialect_name="duckdb",
    )
    assert problems_snapshot(loaded.problems) == snapshot(
        f"[FATAL] Project path is not a directory: `{project_file}`"
    )


def test_load_non_mapping_resource():
    with tmp_project_dir("not-a-resource") as project_dir:
        loaded = load_project(
            project_dir=project_dir,
            project_name="",
            dialect_name="duckdb",
        )
    problem_messages = problems_snapshot(loaded.problems)
    assert "[ERROR] Resource declarations must be mappings" in problem_messages
    assert "Internal error" not in problem_messages


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


@pytest.mark.parametrize(
    "link_name, target",
    [
        ("leak.yml", None),
        ("leak.yaml", Path("..") / "secret.env"),
    ],
)
def test_rejects_out_of_tree_yml_symlink(
    tmp_path: Path, link_name: str, target: Path | None
):
    secret_text = "SUPER_SECRET_VALUE_do_not_leak"
    secret = tmp_path / "secret.env"
    secret.write_text(f"{secret_text}\nnot: valid: yaml: [", encoding="utf-8")

    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "model.yml").write_text(
        make_yml(make_stub_model("safe_model").model_dump(mode="json")),
        encoding="utf-8",
    )
    (project_dir / link_name).symlink_to(secret if target is None else target)

    loaded = load_project(
        project_dir=project_dir,
        project_name="Test",
        dialect_name="duckdb",
    )

    assert all(
        secret_text not in source.contents_text for source in loaded.source_files
    )
    assert all(secret_text not in problem.message for problem in loaded.problems)
    assert all(secret_text not in source.filepath for source in loaded.source_files)
    assert [source.filepath for source in loaded.source_files] == ["model.yml"]
    assert [model.id for model in loaded.project.models] == ["safe_model"]
    assert problems_snapshot(loaded.problems) == snapshot(
        "[ERROR] File would be read from outside the project directory"
    )


def test_does_not_follow_directory_symlink(tmp_path: Path):
    secret_text = "DIR_SECRET_VALUE_do_not_leak"
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.yml").write_text(
        f"id: leaked_model\nbase_sql_table: {secret_text}\n",
        encoding="utf-8",
    )

    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "model.yml").write_text(
        make_yml(make_stub_model("safe_model").model_dump(mode="json")),
        encoding="utf-8",
    )
    (project_dir / "linked").symlink_to(outside)

    loaded = load_project(
        project_dir=project_dir,
        project_name="Test",
        dialect_name="duckdb",
    )

    assert all(
        secret_text not in source.contents_text for source in loaded.source_files
    )
    assert all(secret_text not in problem.message for problem in loaded.problems)
    assert all(secret_text not in source.filepath for source in loaded.source_files)
    assert [source.filepath for source in loaded.source_files] == ["model.yml"]
    assert [model.id for model in loaded.project.models] == ["safe_model"]
    assert all("linked" not in source.filepath for source in loaded.source_files)
    assert all("leaked_model" != model.id for model in loaded.project.models)


def test_resolves_symlinked_project_directory(tmp_path: Path):
    real_dir = tmp_path / "real"
    real_dir.mkdir()
    (real_dir / "model.yml").write_text(
        make_yml(make_stub_model("safe_model").model_dump(mode="json")),
        encoding="utf-8",
    )
    link_dir = tmp_path / "link"
    link_dir.symlink_to(real_dir)

    loaded = load_project(
        project_dir=link_dir,
        project_name="Test",
        dialect_name="duckdb",
    )

    assert loaded.problems == []
    assert [source.filepath for source in loaded.source_files] == ["model.yml"]
    assert [model.id for model in loaded.project.models] == ["safe_model"]


def test_allows_in_tree_yml_symlink(tmp_path: Path):
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "model.yml").write_text(
        make_yml(make_stub_model("safe_model").model_dump(mode="json")),
        encoding="utf-8",
    )
    (project_dir / "alias.yml").symlink_to("model.yml")

    loaded = load_project(
        project_dir=project_dir,
        project_name="Test",
        dialect_name="duckdb",
    )

    assert loaded.problems == []
    assert [source.filepath for source in loaded.source_files] == [
        "alias.yml",
        "model.yml",
    ]
    assert [model.id for model in loaded.project.models] == ["safe_model", "safe_model"]
