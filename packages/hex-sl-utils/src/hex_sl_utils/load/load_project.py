from __future__ import annotations

from pathlib import Path

from pydantic import ValidationError

from ..types import Dialect, DialectName, Project, Resource
from ..types.loaded_project import LoadedProject
from ..types.problems import KeyPath
from ..types.source_file import SourceFile, SourceFileResource
from .context import LoadContext
from .load_resource import load_resource
from .yaml import ryml_parse


def load_project(
    *,
    project_dir: str | Path,
    project_name: str,
    dialect_name: DialectName,
) -> LoadedProject:
    """
    Load a Hex project from a directory into memory.
    """
    ctx = LoadContext()

    try:
        dialect = Dialect(dialect_name)
    except ValidationError:
        ctx.report_problem(
            severity="fatal",
            message=f"Invalid dialect name: {dialect_name}",
            path=[],
        )
        dialect = Dialect("duckdb")  # just to keep things moving along

    project_dir = Path(project_dir)
    loaded_resources: list[Resource] = []
    loaded_source_files: list[SourceFile] = []

    for yml_file_path in get_all_yml_file_paths(project_dir):
        relative_path = yml_file_path.relative_to(project_dir)
        parse_result = parse_yml_file(
            full_path=yml_file_path,
            relative_path=relative_path,
            ctx=ctx,
        )
        resources, source_file = parse_result
        loaded_source_files.append(source_file)
        loaded_resources.extend(resources)

    if not any(r for r in loaded_resources if r.type == "model"):
        ctx.report_problem(
            severity="error",
            message="No valid models found.",
            path=[],
        )

    ctx.project = Project(
        name=project_name,
        resources=loaded_resources,
        dialect=dialect,
    )
    return LoadedProject(
        project=ctx.project,
        problems=ctx.problems,
        source_files=loaded_source_files,
    )


def get_all_yml_file_paths(base_dir: Path) -> list[Path]:
    """
    Get all YML file paths in the project directory.
    """
    if not base_dir.exists():
        return []

    yml_file_paths = list(base_dir.rglob("*.yml"))
    yml_file_paths.extend(base_dir.rglob("*.yaml"))
    return sorted(yml_file_paths)


def parse_yml_file(
    *,
    full_path: Path,
    relative_path: Path,
    ctx: LoadContext,
) -> tuple[list[Resource], SourceFile]:
    """
    Parse a YML file into a set of resources. This can return multiple resources,
    since YML allows many documents in a single file separated by `---` markers.
    """
    source_file = SourceFile(filepath=str(relative_path), contents_text="")
    problem_path: KeyPath = [str(relative_path)]
    try:
        source_file.contents_text = full_path.read_text(encoding="utf-8")
        file_data = ryml_parse(source_file.contents_text)
        file_data = file_data if isinstance(file_data, list) else [file_data]
    except Exception as e:  # noqa: BLE001
        ctx.report_problem(
            severity="error",
            message=f"Invalid YAML in file `{relative_path}`: {e}",
            path=problem_path,
            # json schema validation includes malformed YAML, since that'd be
            # the first step it'd be doing
            validated_by_json_schema=True,
        )
        return [], source_file

    resources: list[Resource] = []
    for resource_data in file_data:
        resource = load_resource(resource_data, ctx=ctx)
        if resource is None:
            source_file.resources.append(
                SourceFileResource(resource_id=None, resource_type="unknown")
            )
        else:
            resources.append(resource)
            resource_type = resource.type if resource.type != "model" else "model"
            source_file.resources.append(
                SourceFileResource(resource_type=resource_type, resource_id=resource.id)
            )

    return resources, source_file
