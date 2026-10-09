"""Build, verify, and refresh dependencies for Hex's Ossie preview releases."""

import argparse
import re
import shutil
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from build_wheels import build_wheels, load_apache_ossie_dependency_revision
from constants import (
    DEFAULT_ASSETS_DIRECTORY,
    DEPENDENCY_LOCK,
    OSSIE_HEX_PACKAGE,
    PYTHON_VERSION,
    WORKSPACE_ROOT,
)
from release_artifacts import verify_release_artifacts, write_release_metadata


def main() -> None:
    """Dispatch the three release-maintenance commands."""
    args = _parse_arguments()
    if args.command == "build":
        _build_preview(
            args.release, args.out_dir.resolve(), require_clean=args.require_clean
        )
    elif args.command == "lock":
        _lock_dependencies()
    else:
        verify_release_artifacts(args.assets)


def _build_preview(release: str, output: Path, *, require_clean: bool = False) -> None:
    """Build wheels, add installation metadata, then verify and copy the payload."""
    _validate_build(release, output)
    hex_revision = _converter_revision(require_clean=require_clean)
    apache_revision = load_apache_ossie_dependency_revision()
    with tempfile.TemporaryDirectory(prefix="ossie-preview-build-") as temporary:
        directory = Path(temporary) / "assets"
        wheels = build_wheels(directory, apache_revision)
        write_release_metadata(
            directory,
            wheels,
            release=release,
            hex_revision=hex_revision,
            apache_revision=apache_revision,
            dependencies=DEPENDENCY_LOCK.read_text(encoding="utf-8"),
        )
        verify_release_artifacts(directory)
        output.parent.mkdir(parents=True, exist_ok=True)
        if output.exists():
            shutil.rmtree(output)
        shutil.copytree(directory, output)
    print(f"Built ossie-preview/{release} assets in {output}")


def _lock_dependencies() -> None:
    """Resolve PyPI dependencies from both wheels, independently of the workspace."""
    with tempfile.TemporaryDirectory(prefix="ossie-preview-lock-") as temporary:
        directory = Path(temporary)
        wheels = build_wheels(
            directory / "wheels", load_apache_ossie_dependency_revision()
        )
        inputs = directory / "wheels.txt"
        inputs.write_text(
            "".join(f"{wheel}\n" for wheel in wheels),
            encoding="utf-8",
        )
        subprocess.run(
            [
                "uv",
                "pip",
                "compile",
                str(inputs),
                "--quiet",
                "--upgrade",
                "--python-version",
                PYTHON_VERSION,
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
                str(DEPENDENCY_LOCK),
            ],
            cwd=WORKSPACE_ROOT,
            check=True,
        )


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("lock", help="Refresh pinned, hashed PyPI dependencies")
    verify = commands.add_parser("verify", help="Verify a complete release payload")
    verify.add_argument("--assets", type=Path, default=DEFAULT_ASSETS_DIRECTORY)
    build = commands.add_parser(
        "build", help="Build wheels and GitHub Release metadata"
    )
    build.add_argument(
        "release",
        nargs="?",
        default=datetime.now(UTC).strftime("v%Y.%m.%d"),
        help="Preview identifier (default: vYYYY.MM.DD in UTC)",
    )
    build.add_argument("--out-dir", type=Path, default=DEFAULT_ASSETS_DIRECTORY)
    build.add_argument(
        "--require-clean",
        action="store_true",
        help="Require committed converter sources",
    )
    return parser.parse_args()


def _validate_build(release: str, output: Path) -> None:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", release):
        raise ValueError(
            "Release identifier must contain only letters, numbers, '.', '_' or '-'"
        )
    if not DEPENDENCY_LOCK.is_file():
        raise ValueError(
            "Run just scripts-ossie-preview-lock before building preview assets"
        )
    if output.exists():
        _validate_output_directory(output)


def _validate_output_directory(output: Path) -> None:
    """Allow replacing generated preview files, including a damaged old build."""
    metadata = {"requirements.txt", "RELEASE_NOTES.md", "SHA256SUMS"}
    if not output.is_dir():
        raise ValueError(f"Output is not a directory: {output}")
    for asset in output.iterdir():
        known = asset.name in metadata or re.fullmatch(
            r"(?:apache_ossie|ossie_hex)-.+\.whl", asset.name
        )
        if asset.is_symlink() or not asset.is_file() or not known:
            raise ValueError(f"Output contains an unrelated file: {asset}")


def _converter_revision(*, require_clean: bool) -> str:
    """Read the converter commit, requiring committed sources for CI builds."""
    if require_clean:
        changes = subprocess.check_output(
            [
                "git",
                "status",
                "--porcelain",
                "--",
                str(OSSIE_HEX_PACKAGE.relative_to(WORKSPACE_ROOT)),
            ],
            cwd=WORKSPACE_ROOT,
            text=True,
        )
        if changes:
            raise ValueError(
                "Commit converter changes before preparing a published preview"
            )
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=WORKSPACE_ROOT, text=True
    ).strip()


if __name__ == "__main__":
    main()
