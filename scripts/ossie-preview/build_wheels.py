"""Build the converter and canonical Apache Ossie as standalone Python wheels."""

import re
import shutil
import subprocess
import tempfile
import tomllib
import urllib.request
import zipfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from constants import (
    APACHE_OSSIE_SOURCE,
    HEX_PREVIEW,
    SOURCES_FILE,
    WORKSPACE_ROOT,
    PreviewConverter,
)


@dataclass(frozen=True)
class ConverterSource:
    commit: str
    directory: str


def build_wheels(
    directory: Path, source: ConverterSource, converter: PreviewConverter = HEX_PREVIEW
) -> list[Path]:
    """Build the selected converter and matching SDK from one upstream snapshot."""
    directory.mkdir(parents=True)
    with _apache_checkout(source.commit) as checkout:
        _build_upstream_wheel(checkout, "python", directory)
        _build_upstream_wheel(checkout, source.directory, directory)
    (directory / ".gitignore").unlink(missing_ok=True)
    wheels = sorted(directory.glob("*.whl"))
    expected = {"apache_ossie", converter.package_name.replace("-", "_")}
    if len(wheels) != 2 or any(
        not wheel.name.endswith("-py3-none-any.whl")
        or wheel.name.split("-", 1)[0] not in expected
        for wheel in wheels
    ):
        raise ValueError(
            "Expected the converter and SDK as platform-independent wheels"
        )
    return wheels


def load_converter_source(converter: PreviewConverter) -> ConverterSource:
    """Resolve a converter override or the shared Apache commit before downloading."""
    data = tomllib.loads(SOURCES_FILE.read_text(encoding="utf-8"))
    entry = data["converters"][converter.name]
    commit = entry.get("commit", data["commit"])
    if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("Apache Ossie must be pinned to a full Git commit")
    directory = entry["directory"]
    if not isinstance(directory, str):
        raise TypeError("Converter directory must be a relative path under converters/")
    path = PurePosixPath(directory)
    if (
        "\\" in directory
        or path.is_absolute()
        or ".." in path.parts
        or path.parts[:1] != ("converters",)
        or len(path.parts) < 2
    ):
        raise ValueError(
            "Converter directory must be a relative path under converters/"
        )
    return ConverterSource(commit=commit, directory=directory)


@contextmanager
def _apache_checkout(revision: str) -> Iterator[Path]:
    """Download one immutable source snapshot without retaining a checkout."""
    with tempfile.TemporaryDirectory(prefix="apache-ossie-source-") as temporary:
        source = Path(temporary)
        archive = source / "ossie.zip"
        url = f"{APACHE_OSSIE_SOURCE.removesuffix('.git')}/archive/{revision}.zip"
        with urllib.request.urlopen(url, timeout=120) as response:
            archive.write_bytes(response.read())
        with zipfile.ZipFile(archive) as snapshot:
            snapshot.extractall(source)
        yield source / f"ossie-{revision}"


def _build_upstream_wheel(checkout: Path, subdirectory: str, output: Path) -> None:
    """Include repository notices in standalone upstream packages."""
    package = checkout / subdirectory
    for name in ("LICENSE", "NOTICE"):
        shutil.copy2(checkout / name, package / name)
    _build_wheel(package, output)


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
