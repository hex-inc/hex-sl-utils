"""Build the converter and canonical Apache Ossie as standalone Python wheels."""

import re
import shutil
import subprocess
import tempfile
import tomllib
import urllib.request
import zipfile
from pathlib import Path

from constants import APACHE_OSSIE_SOURCE, OSSIE_HEX_PACKAGE, WORKSPACE_ROOT


def build_wheels(directory: Path, revision: str) -> list[Path]:
    """Build unpublished packages and require platform-independent wheels."""
    directory.mkdir(parents=True)
    _build_workspace_wheel(directory)
    _build_apache_ossie_wheel(revision, directory)
    # uv creates this local build marker; it is not a release asset.
    (directory / ".gitignore").unlink(missing_ok=True)
    wheels = sorted(directory.glob("*.whl"))
    if len(wheels) != 2 or any(
        not wheel.name.endswith("-py3-none-any.whl") for wheel in wheels
    ):
        raise ValueError("Expected two platform-independent Python wheels")
    return wheels


def load_apache_ossie_dependency_revision() -> str:
    """Read and validate the converter's canonical Apache development pin."""
    data = tomllib.loads((OSSIE_HEX_PACKAGE / "pyproject.toml").read_text())
    source = data["tool"]["uv"]["sources"]["apache-ossie"]
    if (
        source.get("git") != APACHE_OSSIE_SOURCE
        or source.get("subdirectory") != "python"
    ):
        raise ValueError(
            "Preview wheels must be built from upstream apache/ossie/python"
        )
    revision = source.get("rev", "")
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("Apache Ossie must be pinned to a full Git commit")
    return revision


def _build_workspace_wheel(output: Path) -> None:
    _build_wheel(OSSIE_HEX_PACKAGE, output)


def _build_apache_ossie_wheel(revision: str, output: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="apache-ossie-source-") as temporary:
        source = Path(temporary)
        archive = source / "ossie.zip"
        url = f"{APACHE_OSSIE_SOURCE.removesuffix('.git')}/archive/{revision}.zip"
        with urllib.request.urlopen(url, timeout=120) as response:
            archive.write_bytes(response.read())
        with zipfile.ZipFile(archive) as snapshot:
            snapshot.extractall(source)
        checkout = source / f"ossie-{revision}"
        # The upstream Python project omits the repository notices. Include
        # them in its standalone wheel without changing the package source.
        for name in ("LICENSE", "NOTICE"):
            shutil.copy2(checkout / name, checkout / "python" / name)
        _build_wheel(checkout / "python", output)


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
