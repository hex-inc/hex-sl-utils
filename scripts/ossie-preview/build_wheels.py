"""Build the preview bundle's unpublished packages as standalone wheels."""

import shutil
import subprocess
import tempfile
import tomllib
from pathlib import Path

from constants import (
    BUNDLE_PROJECT,
    CONVERTER_SOURCE,
    RELEASE_PACKAGES,
    WORKSPACE_ROOT,
)


def build_wheels(directory: Path) -> list[Path]:
    """Build unpublished packages and require platform-independent wheels."""
    directory.mkdir(parents=True)
    for name, package in load_package_sources().items():
        checkout = (
            CONVERTER_SOURCE / "ossie" if name == "apache-ossie" else CONVERTER_SOURCE
        )
        _build_source_wheel(package, directory, checkout=checkout)
    # uv creates this local build marker; it is not a release asset.
    (directory / ".gitignore").unlink(missing_ok=True)
    wheels = sorted(directory.glob("*.whl"))
    names = sorted(wheel.name.split("-", 1)[0].replace("_", "-") for wheel in wheels)
    if names != sorted(RELEASE_PACKAGES) or any(
        not wheel.name.endswith("-py3-none-any.whl") for wheel in wheels
    ):
        raise ValueError("Expected one platform-independent wheel per bundle package")
    return wheels


def load_package_sources() -> dict[str, Path]:
    """Require bundle sources and shared Ossie to agree inside the submodule."""
    data = tomllib.loads((BUNDLE_PROJECT / "pyproject.toml").read_text())
    sources = data["tool"]["uv"]["sources"]
    packages: dict[str, Path] = {}
    for name in RELEASE_PACKAGES:
        source = sources[name]
        if "path" not in source:
            raise ValueError(
                "Preview sources must be paths inside the pinned submodule"
            )
        package = (BUNDLE_PROJECT / source["path"]).resolve()
        if not package.is_relative_to(CONVERTER_SOURCE.resolve()):
            raise ValueError("Preview sources must stay inside the pinned submodule")
        if not (package / "pyproject.toml").is_file():
            raise ValueError("Initialize the converter with just setup-scripts")
        packages[name] = package

    for name, package in packages.items():
        metadata = tomllib.loads((package / "pyproject.toml").read_text())
        if metadata["project"]["name"] != name:
            raise ValueError(f"Bundle source does not declare package {name}")
        source = (
            metadata.get("tool", {})
            .get("uv", {})
            .get("sources", {})
            .get("apache-ossie")
        )
        if source is not None and (
            "path" not in source
            or (package / source["path"]).resolve() != packages["apache-ossie"]
        ):
            raise ValueError(
                "Converters must use the bundle's shared Apache Ossie source"
            )
    return packages


def _build_source_wheel(source: Path, output: Path, *, checkout: Path) -> None:
    if not (source / "pyproject.toml").is_file():
        raise ValueError("Initialize the converter with just setup-scripts")
    with tempfile.TemporaryDirectory(prefix="ossie-preview-source-") as temporary:
        package = Path(temporary) / source.name
        shutil.copytree(
            source,
            package,
            ignore=shutil.ignore_patterns(".venv", "__pycache__", ".*cache", "dist"),
        )
        _include_notices(checkout, package)
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
