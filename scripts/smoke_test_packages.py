"""Smoke-test every built distribution artifact in an isolated environment."""

import os
import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path

from packaging.utils import (
    canonicalize_name,
    parse_sdist_filename,
    parse_wheel_filename,
)
from packaging.version import Version

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = ROOT / "packages"
DIST = ROOT / "dist"


@dataclass(frozen=True, slots=True)
class Package:
    """A publishable workspace package and its smoke test."""

    name: str
    version: Version
    smoke_test: Path
    smoke_test_python_versions: tuple[str, ...]


def smoke_test_python_versions(
    pyproject_data: dict[str, object], pyproject: Path
) -> tuple[str, ...]:
    """Return the package's declared smoke-test Python versions."""
    match pyproject_data:
        case {"tool": {"smoke-test": {"python-versions": versions}}}:
            pass
        case _:
            raise ValueError(
                f"{pyproject} must declare tool.smoke-test.python-versions"
            )

    if not isinstance(versions, list):
        raise TypeError(f"{pyproject}: tool.smoke-test.python-versions must be a list")

    if (
        len(versions) < 2
        or not all(isinstance(version, str) and version for version in versions)
        or len(set(versions)) != len(versions)
    ):
        raise ValueError(
            f"{pyproject}: tool.smoke-test.python-versions must contain at least "
            "two distinct Python versions"
        )

    parsed_versions = [Version(version) for version in versions]
    if parsed_versions != sorted(parsed_versions):
        raise ValueError(
            f"{pyproject}: tool.smoke-test.python-versions must be ordered from "
            "floor to ceiling"
        )
    return tuple(versions)


def workspace_packages(packages_dir: Path = PACKAGES) -> list[Package]:
    """Return publishable workspace packages in stable path order."""
    packages: list[Package] = []
    for pyproject in sorted(packages_dir.glob("*/pyproject.toml")):
        pyproject_data = tomllib.loads(pyproject.read_text())
        project = pyproject_data["project"]
        packages.append(
            Package(
                name=project["name"],
                version=Version(project["version"]),
                smoke_test=pyproject.parent / "tests" / "smoke_test.py",
                smoke_test_python_versions=smoke_test_python_versions(
                    pyproject_data, pyproject
                ),
            )
        )
    return packages


def package_artifacts(package: Package, dist_dir: Path = DIST) -> list[Path]:
    """Return the package's one wheel and one source distribution."""
    expected_name = canonicalize_name(package.name)
    artifacts: list[Path] = []

    for artifact in sorted(dist_dir.glob("*.whl")):
        name, version, _, _ = parse_wheel_filename(artifact.name)
        if canonicalize_name(name) == expected_name and version == package.version:
            artifacts.append(artifact)

    for artifact in sorted(dist_dir.glob("*.tar.gz")):
        name, version = parse_sdist_filename(artifact.name)
        if canonicalize_name(name) == expected_name and version == package.version:
            artifacts.append(artifact)

    if len(artifacts) != 2:
        raise ValueError(
            f"Expected one wheel and one source distribution for "
            f"{package.name} {package.version}, found {len(artifacts)}"
        )
    return artifacts


def main() -> None:
    """Install and smoke-test each artifact in its own environment."""
    packages = workspace_packages()
    if not packages:
        raise SystemExit("No publishable packages found under packages/")

    for package in packages:
        if not package.smoke_test.is_file():
            raise FileNotFoundError(
                f"Missing smoke test for {package.name}: {package.smoke_test}"
            )

        for python_version in package.smoke_test_python_versions:
            for artifact in package_artifacts(package):
                print(
                    f"Smoke-testing {package.name} {artifact.name} with "
                    f"Python {python_version}",
                    flush=True,
                )
                subprocess.run(
                    [
                        "uv",
                        "run",
                        "--python",
                        python_version,
                        "--isolated",
                        "--no-project",
                        "--with",
                        str(artifact),
                        "--",
                        "python",
                        str(package.smoke_test),
                    ],
                    cwd=ROOT,
                    check=True,
                    env={
                        **os.environ,
                        "UV_PYTHON_DOWNLOADS": "automatic",
                        "UV_PYTHON_PREFERENCE": "system",
                    },
                )


if __name__ == "__main__":
    main()
