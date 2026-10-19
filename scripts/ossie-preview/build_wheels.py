"""Build the converter and its Apache Ossie dependency as standalone wheels."""

import shutil
import subprocess
import tempfile
import tomllib
from pathlib import Path

from constants import (
    CONVERTER_SOURCE,
    OSSIE_HEX_PACKAGE,
    WORKSPACE_ROOT,
)


def build_wheels(directory: Path) -> list[Path]:
    """Build unpublished packages and require platform-independent wheels."""
    directory.mkdir(parents=True)
    _build_source_wheel(OSSIE_HEX_PACKAGE, directory)
    _build_source_wheel(load_apache_ossie_package(), directory)
    # uv creates this local build marker; it is not a release asset.
    (directory / ".gitignore").unlink(missing_ok=True)
    wheels = sorted(directory.glob("*.whl"))
    if len(wheels) != 2 or any(
        not wheel.name.endswith("-py3-none-any.whl") for wheel in wheels
    ):
        raise ValueError("Expected two platform-independent Python wheels")
    return wheels


def load_apache_ossie_package() -> Path:
    """Follow the converter's Apache Ossie source within the pinned submodule."""
    data = tomllib.loads((OSSIE_HEX_PACKAGE / "pyproject.toml").read_text())
    source = data["tool"]["uv"]["sources"]["apache-ossie"]
    if "path" not in source:
        raise ValueError(
            "Preview builds require an Apache Ossie path inside the submodule"
        )
    package = (OSSIE_HEX_PACKAGE / source["path"]).resolve()
    if not package.is_relative_to(CONVERTER_SOURCE.resolve()):
        raise ValueError("Apache Ossie source must stay inside the pinned submodule")
    return package


def _build_source_wheel(source: Path, output: Path) -> None:
    if not (source / "pyproject.toml").is_file():
        raise ValueError("Initialize the converter with just setup-scripts")
    with tempfile.TemporaryDirectory(prefix="ossie-preview-source-") as temporary:
        package = Path(temporary) / source.name
        shutil.copytree(
            source,
            package,
            ignore=shutil.ignore_patterns(".venv", "__pycache__", ".*cache", "dist"),
        )
        _include_notices(CONVERTER_SOURCE, package)
        _build_wheel(package, output)


def _include_notices(checkout: Path, package: Path) -> None:
    """Package repository notices in a temporary tree, leaving upstream clean."""
    for name in ("LICENSE", "NOTICE"):
        shutil.copy2(checkout / name, package / name)
    pyproject = package / "pyproject.toml"
    metadata = pyproject.read_text()
    if "license-files" not in tomllib.loads(metadata)["project"]:
        metadata = metadata.replace(
            "[project]\n", '[project]\nlicense-files = ["LICENSE", "NOTICE"]\n', 1
        )
        pyproject.write_text(metadata)


def _build_wheel(package: Path, output: Path) -> None:
    subprocess.run(
        [
            "uv",
            "build",
            str(package),
            "--wheel",
            "--no-sources",
            "--out-dir",
            str(output),
        ],
        cwd=WORKSPACE_ROOT,
        check=True,
    )
