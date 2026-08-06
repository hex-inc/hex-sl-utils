"""Build every publishable distribution in the uv workspace."""

from __future__ import annotations

import subprocess
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = ROOT / "packages"
DIST = ROOT / "dist"


def package_names(packages_dir: Path = PACKAGES) -> list[str]:
    """Return publishable project names in stable path order."""
    names: list[str] = []
    for pyproject in sorted(packages_dir.glob("*/pyproject.toml")):
        project_data: dict[str, Any] = tomllib.loads(pyproject.read_text())
        names.append(project_data["project"]["name"])
    return names


def main() -> None:
    """Build source and wheel distributions without uv source overrides."""
    names = package_names()
    if not names:
        raise SystemExit("No publishable packages found under packages/")

    for name in names:
        subprocess.run(
            [
                "uv",
                "build",
                "--package",
                name,
                "--out-dir",
                str(DIST / name),
                "--no-sources",
            ],
            cwd=ROOT,
            check=True,
        )


if __name__ == "__main__":
    main()
