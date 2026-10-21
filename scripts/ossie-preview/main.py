"""Build and verify Hex's Ossie preview releases."""

import argparse
import re
import shutil
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from build_wheels import build_wheels
from constants import (
    CONVERTER_SOURCE,
    DEFAULT_ASSETS_DIRECTORY,
    OSSIE_HEX_PACKAGE,
    WORKSPACE_ROOT,
)
from release_artifacts import verify_release_artifacts, write_release_metadata


def main() -> None:
    """Dispatch the release build and verification commands."""
    args = _parse_arguments()
    if args.command == "build":
        _build_preview(
            args.release, args.out_dir.resolve(), require_clean=args.require_clean
        )
    elif args.command == "verify":
        verify_release_artifacts(args.assets)
    else:
        raise ValueError(f"Unexpected command: {args.command}")


def _build_preview(release: str, output: Path, *, require_clean: bool = False) -> None:
    """Build wheels, add installation metadata, then verify and copy the payload."""
    _validate_build(release, output)
    hex_revision = _converter_revision(require_clean=require_clean)
    workspace_revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=WORKSPACE_ROOT, text=True
    ).strip()
    dependencies = _export_dependencies()
    with tempfile.TemporaryDirectory(prefix="ossie-preview-build-") as temporary:
        directory = Path(temporary) / "assets"
        wheels = build_wheels(directory)
        write_release_metadata(
            directory,
            wheels,
            release=release,
            hex_revision=hex_revision,
            workspace_revision=workspace_revision,
            dependencies=dependencies,
        )
        verify_release_artifacts(directory)
        output.parent.mkdir(parents=True, exist_ok=True)
        if output.exists():
            shutil.rmtree(output)
        shutil.copytree(directory, output)
    print(f"Built ossie-preview/{release} assets in {output}")


def _export_dependencies() -> str:
    """Export hashed runtime pins, replacing upstream local packages with wheels."""
    return subprocess.check_output(
        [
            "uv",
            "export",
            "--project",
            str(OSSIE_HEX_PACKAGE),
            "--locked",
            "--no-dev",
            "--no-emit-project",
            "--no-emit-package",
            "apache-ossie",
            "--format",
            "requirements-txt",
            "--no-header",
            "--no-annotate",
        ],
        cwd=WORKSPACE_ROOT,
        text=True,
    )


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
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
    if not (CONVERTER_SOURCE / "converters" / "hex" / "pyproject.toml").is_file():
        raise ValueError("Initialize the converter with just setup-scripts")
    revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=CONVERTER_SOURCE, text=True
    ).strip()
    if require_clean:
        changes = subprocess.check_output(
            [
                "git",
                "status",
                "--porcelain",
                "--",
                str(CONVERTER_SOURCE.relative_to(WORKSPACE_ROOT)),
            ],
            cwd=WORKSPACE_ROOT,
            text=True,
        )
        if changes:
            raise ValueError(
                "Commit converter changes and its submodule pin before publishing"
            )
    return revision


if __name__ == "__main__":
    main()
