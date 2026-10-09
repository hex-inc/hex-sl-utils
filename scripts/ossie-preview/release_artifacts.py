"""Write and verify the installation metadata in an Ossie preview payload."""

import hashlib
import re
from pathlib import Path
from urllib.parse import quote

from constants import APACHE_OSSIE_SOURCE, PYTHON_VERSION, RELEASE_REPOSITORY


def write_release_metadata(
    directory: Path,
    wheels: list[Path],
    *,
    release: str,
    hex_revision: str,
    apache_revision: str,
    dependencies: str,
) -> None:
    """Write hashed installation requirements, source provenance, and checksums."""
    _write_requirements(directory, wheels, release, dependencies)
    _write_release_notes(directory, release, hex_revision, apache_revision)
    _write_checksums(directory)


def verify_release_artifacts(directory: Path) -> None:
    """Require the exact release inventory and verify every asset's checksum."""
    digests = _read_checksums(directory / "SHA256SUMS")
    _verify_inventory(directory, set(digests))
    for name, digest in digests.items():
        asset = directory / name
        if asset.is_symlink() or not asset.is_file() or _sha256(asset) != digest:
            raise ValueError(f"Checksum mismatch: {name}")


def _write_requirements(
    directory: Path, wheels: list[Path], release: str, dependencies: str
) -> None:
    tag = f"ossie-preview/{release}"
    base = f"https://github.com/{RELEASE_REPOSITORY}/releases/download/{quote(tag, safe='')}"
    requirements = (
        "".join(
            f"{base}/{wheel.name} \\\n    --hash=sha256:{_sha256(wheel)}\n"
            for wheel in wheels
        )
        + dependencies
    )
    (directory / "requirements.txt").write_text(requirements, encoding="utf-8")


def _write_release_notes(
    directory: Path,
    release: str,
    hex_revision: str,
    apache_revision: str,
) -> None:
    (directory / "RELEASE_NOTES.md").write_text(
        f"# Preview of Hex's Apache Ossie converter ({release})\n\n"
        f"- Hex converter: [commit](https://github.com/{RELEASE_REPOSITORY}/commit/"
        f"{hex_revision})\n"
        f"- Apache Ossie: [commit]({APACHE_OSSIE_SOURCE.removesuffix('.git')}/commit/"
        f"{apache_revision})\n"
        f"- Runtime: Python {PYTHON_VERSION}\n"
        "- Runtime dependencies: pinned and hashed in `requirements.txt`\n\n"
        f"See the [preview guide](https://github.com/{RELEASE_REPOSITORY}/blob/"
        f"{hex_revision}/scripts/ossie-preview/README.md) for installation and "
        "release details.\n",
        encoding="utf-8",
    )


def _write_checksums(directory: Path) -> None:
    checksums = "".join(
        f"{_sha256(asset)}  {asset.name}\n" for asset in sorted(directory.iterdir())
    )
    (directory / "SHA256SUMS").write_text(checksums, encoding="utf-8")


def _read_checksums(manifest: Path) -> dict[str, str]:
    if manifest.is_symlink() or not manifest.is_file():
        raise ValueError("Expected a release checksum manifest")
    digests: dict[str, str] = {}
    for line in manifest.read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        if (
            not re.fullmatch(r"[0-9a-f]{64}", digest)
            or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", name)
            or name == "SHA256SUMS"
            or name in digests
        ):
            raise ValueError(f"Invalid checksum entry: {name}")
        digests[name] = digest
    return digests


def _verify_inventory(directory: Path, listed: set[str]) -> None:
    wheels = list(directory.glob("*-py3-none-any.whl"))
    if (
        len(wheels) != 2
        or sum(wheel.name.startswith("apache_ossie-") for wheel in wheels) != 1
        or sum(wheel.name.startswith("ossie_hex-") for wheel in wheels) != 1
    ):
        raise ValueError("Expected exactly the two wheels and release metadata")
    expected = {"requirements.txt", "RELEASE_NOTES.md"} | {
        wheel.name for wheel in wheels
    }
    actual = {asset.name for asset in directory.iterdir()}
    if listed != expected or actual != expected | {"SHA256SUMS"}:
        raise ValueError("Expected exactly the two wheels and release metadata")


def _sha256(path: Path) -> str:
    """Return the digest used to verify a release asset."""
    with path.open("rb") as file:
        return hashlib.file_digest(file, "sha256").hexdigest()
