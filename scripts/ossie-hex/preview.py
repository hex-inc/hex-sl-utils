"""Build the wheel assets consumed by the Hex CLI's Ossie preview installation."""

import argparse
import email
import hashlib
import html
import re
import shutil
import subprocess
import tempfile
import tomllib
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "packages" / "ossie-hex"
LOCK = Path(__file__).with_name("requirements.lock")
UPSTREAM = "https://github.com/apache/ossie.git"
REPOSITORY = "hex-inc/hex-sl-utils"
PYTHON = "3.12"
INDEX = "https://hex-internal-pypi-index.hex.tech"
PREFIX = "ossie-preview"


def run(*args: str | Path, cwd: Path = ROOT) -> None:
    """Run a real build or dependency-resolution command."""
    subprocess.run([str(arg) for arg in args], cwd=cwd, check=True)


def sha256(path: Path) -> str:
    """Return the digest used to verify a release asset."""
    with path.open("rb") as file:
        return hashlib.file_digest(file, "sha256").hexdigest()


def upstream_revision() -> str:
    """Use the converter's development pin as the preview's upstream source."""
    data = tomllib.loads((PACKAGE / "pyproject.toml").read_text())
    source = data["tool"]["uv"]["sources"]["apache-ossie"]
    if source.get("git") != UPSTREAM or source.get("subdirectory") != "python":
        raise ValueError(
            "Preview wheels must be built from upstream apache/ossie/python"
        )
    revision = source.get("rev", "")
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("Apache Ossie must be pinned to a full Git commit")
    return revision


def build_wheels(directory: Path, revision: str) -> list[Path]:
    """Build both unpublished packages; only CI/build machines need source code."""
    directory.mkdir(parents=True)
    run("uv", "build", PACKAGE, "--wheel", "--no-sources", "--out-dir", directory)
    with tempfile.TemporaryDirectory(prefix="apache-ossie-source-") as temporary:
        source = Path(temporary)
        archive = source / "ossie.zip"
        url = f"https://github.com/apache/ossie/archive/{revision}.zip"
        with urllib.request.urlopen(url, timeout=120) as response:
            archive.write_bytes(response.read())
        with zipfile.ZipFile(archive) as snapshot:
            snapshot.extractall(source)
        checkout = source / f"ossie-{revision}"
        # The upstream Python project does not include the repository notices.
        # Preserve them in the standalone wheel without changing its source code.
        for name in ("LICENSE", "NOTICE"):
            shutil.copy2(checkout / name, checkout / "python" / name)
        run(
            "uv",
            "build",
            checkout / "python",
            "--wheel",
            "--no-sources",
            "--out-dir",
            directory,
        )
    wheels = sorted(directory.glob("*.whl"))
    if len(wheels) != 2 or any(
        not wheel.name.endswith("-py3-none-any.whl") for wheel in wheels
    ):
        raise ValueError("Expected two platform-independent Python wheels")
    return wheels


def lock_dependencies() -> None:
    """Resolve consumer dependencies from wheel metadata and PyPI, not the workspace."""
    with tempfile.TemporaryDirectory(prefix="ossie-preview-lock-") as temporary:
        directory = Path(temporary)
        wheels = build_wheels(directory / "wheels", upstream_revision())
        inputs = directory / "requirements.in"
        inputs.write_text(
            Path(__file__).with_name("requirements.in").read_text(encoding="utf-8")
            + "".join(f"{wheel}\n" for wheel in wheels),
            encoding="utf-8",
        )
        run(
            "uv",
            "pip",
            "compile",
            inputs,
            "--quiet",
            "--upgrade",
            "--python-version",
            PYTHON,
            "--universal",
            "--only-binary",
            ":all:",
            "--generate-hashes",
            "--no-header",
            "--no-annotate",
            "--no-emit-package",
            "ossie-hex",
            "--no-emit-package",
            "apache-ossie",
            "--output-file",
            LOCK,
        )


def write_index(directory: Path, wheels: list[Path]) -> list[str]:
    """Create a release-scoped simple index without changing upstream versions."""
    index = directory / "simple"
    index.mkdir()
    packages: list[str] = []
    requirements: list[str] = []
    for wheel in wheels:
        with zipfile.ZipFile(wheel) as package:
            metadata_files = [
                name
                for name in package.namelist()
                if name.endswith(".dist-info/METADATA")
            ]
            if len(metadata_files) != 1:
                raise ValueError(f"Expected one package metadata file in {wheel.name}")
            metadata = email.message_from_bytes(package.read(metadata_files[0]))
        name = re.sub(r"[-_.]+", "-", str(metadata["Name"])).lower()
        version = str(metadata["Version"])
        digest = sha256(wheel)
        package_index = index / name
        package_index.mkdir()
        (package_index / "index.html").write_text(
            "<!doctype html><html><body>\n"
            f'<a href="../../{html.escape(wheel.name)}#sha256={digest}">'
            f"{html.escape(wheel.name)}</a>\n</body></html>\n",
            encoding="utf-8",
        )
        packages.append(f'<a href="{name}/">{name}</a>')
        requirements.append(f"{name}=={version} \\\n    --hash=sha256:{digest}\n")
    (index / "index.html").write_text(
        "<!doctype html><html><body>\n" + "\n".join(packages) + "\n</body></html>\n",
        encoding="utf-8",
    )
    return requirements


def build_preview(release: str, output: Path, replace: bool = False) -> None:
    """Assemble an immutable preview and its own Python package index."""
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", release):
        raise ValueError(
            "Release identifier must contain only letters, numbers, '.', '_' or '-'"
        )
    if not LOCK.is_file():
        raise ValueError("Run just lock-ossie-preview before building preview assets")
    if output.exists():
        if not replace:
            raise ValueError(
                f"Output already exists: {output}; use --replace for a local rebuild"
            )
        # Only replace a complete payload previously generated by this script.
        checksums_file = output / "SHA256SUMS"
        names = {
            line.split("  ", 1)[1] for line in checksums_file.read_text().splitlines()
        }
        assets = list(output.rglob("*"))
        if names | {"SHA256SUMS"} != {
            asset.relative_to(output).as_posix() for asset in assets if asset.is_file()
        }:
            raise ValueError(
                "Refusing to replace an output directory with unrelated files"
            )
        if any(asset.is_symlink() for asset in assets) or not (
            output / "SOURCES.txt"
        ).read_text().startswith(f"ossie-hex https://github.com/{REPOSITORY} "):
            raise ValueError(
                "Refusing to replace a directory that is not a preview payload"
            )
    changes = subprocess.check_output(
        ["git", "status", "--porcelain", "--", "packages/ossie-hex"],
        cwd=ROOT,
        text=True,
    )
    if changes:
        raise ValueError(
            "Commit converter changes before building a preview with source provenance"
        )
    hex_revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
    ).strip()
    revision = upstream_revision()
    base = f"{INDEX}/{PREFIX}/{release}"
    with tempfile.TemporaryDirectory(prefix="ossie-preview-build-") as temporary:
        directory = Path(temporary) / "assets"
        wheels = build_wheels(directory, revision)
        requirements = (
            "--index-url https://pypi.org/simple\n"
            f"--extra-index-url {base}/simple/\n\n"
            + "".join(write_index(directory, wheels))
            + LOCK.read_text(encoding="utf-8")
        )
        (directory / "requirements.txt").write_text(requirements, encoding="utf-8")
        (directory / "SOURCES.txt").write_text(
            f"ossie-hex https://github.com/{REPOSITORY} {hex_revision} packages/ossie-hex\n"
            f"apache-ossie {UPSTREAM.removesuffix('.git')} {revision} python\n",
            encoding="utf-8",
        )
        (directory / "RELEASE_NOTES.md").write_text(
            f"# Hex Ossie preview {release}\n\n"
            "Hex-managed preview artifacts built from pinned source commits. "
            "Apache owns the official Ossie and converter release process; "
            "these assets are hosted on Hex's Python package index, "
            "not published to public PyPI.\n\n"
            f"- Hex converter: `{hex_revision}`\n"
            f"- Upstream Apache Ossie: `{revision}`\n"
            f"- Runtime: Python {PYTHON}\n"
            "- Published runtime dependencies: pinned and hashed in `requirements.txt`\n\n"
            f"- Installation: {base}/requirements.txt\n\n"
            "Each preview has a separate simple index and immutable wheel URLs, "
            "so Apache's package versions remain unchanged. No Git or package "
            "compilation is required on consumer machines.\n",
            encoding="utf-8",
        )
        checksums = "".join(
            f"{sha256(asset)}  {asset.relative_to(directory).as_posix()}\n"
            for asset in sorted(directory.rglob("*"))
            if asset.is_file()
        )
        (directory / "SHA256SUMS").write_text(checksums, encoding="utf-8")
        output.parent.mkdir(parents=True, exist_ok=True)
        if output.exists():
            shutil.rmtree(output)
        shutil.copytree(directory, output)
    print(f"Built {base}/requirements.txt in {output}")


def main() -> None:
    """Build release assets or explicitly refresh the published dependency lock."""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("lock", help="Refresh pinned, hashed PyPI dependencies")
    build = commands.add_parser(
        "build", help="Build wheels, a simple index, and release metadata"
    )
    build.add_argument(
        "release", help="Preview identifier; index path is ossie-preview/<identifier>"
    )
    build.add_argument("--out-dir", type=Path, default=ROOT / "dist" / "ossie-preview")
    build.add_argument(
        "--replace",
        action="store_true",
        help="Replace an existing local preview payload",
    )
    args = parser.parse_args()
    if args.command == "lock":
        lock_dependencies()
    else:
        build_preview(args.release, args.out_dir.resolve(), args.replace)


if __name__ == "__main__":
    main()
