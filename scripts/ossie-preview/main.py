"""Build and verify Ossie converter preview releases."""

import argparse
import re
import shutil
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from build_wheels import build_wheels, load_converter_source
from constants import (
    CONVERTERS,
    HEX_PREVIEW,
    PYTHON_VERSION,
    WORKSPACE_ROOT,
    PreviewConverter,
)
from release_artifacts import verify_release_artifacts, write_release_metadata


def main() -> None:
    """Dispatch preview building and artifact verification."""
    args = _parse_arguments()
    converter = CONVERTERS[args.converter]
    if args.command == "build":
        _build_preview(
            args.release,
            (args.out_dir or converter.assets_directory).resolve(),
            converter=converter,
            require_clean=args.require_clean,
        )
    else:
        verify_release_artifacts(args.assets or converter.assets_directory, converter)


def _build_preview(
    release: str,
    output: Path,
    *,
    converter: PreviewConverter = HEX_PREVIEW,
    require_clean: bool = False,
) -> None:
    """Build wheels, add installation metadata, then verify and copy the payload."""
    _validate_build(release, output, converter)
    publisher_revision = _publisher_revision(require_clean=require_clean)
    source = load_converter_source(converter)
    with tempfile.TemporaryDirectory(prefix="ossie-preview-build-") as temporary:
        working = Path(temporary)
        directory = working / "assets"
        wheels = build_wheels(directory, source, converter)
        dependencies = _resolve_dependencies(wheels, converter, working)
        write_release_metadata(
            directory,
            wheels,
            release=release,
            publisher_revision=publisher_revision,
            apache_revision=source.commit,
            dependencies=dependencies,
            converter=converter,
        )
        verify_release_artifacts(directory, converter)
        output.parent.mkdir(parents=True, exist_ok=True)
        if output.exists():
            shutil.rmtree(output)
        shutil.copytree(directory, output)
    print(f"Built {converter.tag_prefix}/{release} assets in {output}")


def _resolve_dependencies(
    wheels: list[Path], converter: PreviewConverter, working: Path
) -> str:
    """Resolve fresh PyPI pins and hashes from the wheels being published."""
    inputs = working / "wheels.txt"
    inputs.write_text("".join(f"{wheel}\n" for wheel in wheels), encoding="utf-8")
    requirements = working / "dependencies.txt"
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
            converter.package_name,
            "--no-emit-package",
            "apache-ossie",
            "--output-file",
            str(requirements),
        ],
        cwd=WORKSPACE_ROOT,
        check=True,
    )
    return requirements.read_text(encoding="utf-8")


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    verify = commands.add_parser("verify", help="Verify a complete release payload")
    verify.add_argument("--assets", type=Path)
    build = commands.add_parser(
        "build", help="Build wheels and GitHub Release metadata"
    )
    build.add_argument(
        "release",
        nargs="?",
        default=datetime.now(UTC).strftime("v%Y.%m.%d"),
        help="Preview identifier (default: vYYYY.MM.DD in UTC)",
    )
    build.add_argument("--out-dir", type=Path)
    build.add_argument(
        "--require-clean",
        action="store_true",
        help="Require committed publisher configuration",
    )
    for command in (build, verify):
        command.add_argument("--converter", choices=CONVERTERS, default="hex")
    return parser.parse_args()


def _validate_build(release: str, output: Path, converter: PreviewConverter) -> None:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", release):
        raise ValueError(
            "Release identifier must contain only letters, numbers, '.', '_' or '-'"
        )
    if output.exists():
        _validate_output_directory(output, converter)


def _validate_output_directory(output: Path, converter: PreviewConverter) -> None:
    """Allow replacing generated preview files, including a damaged old build."""
    metadata = {"requirements.txt", "RELEASE_NOTES.md", "SHA256SUMS"}
    converter_wheel = re.escape(converter.package_name.replace("-", "_"))
    if not output.is_dir():
        raise ValueError(f"Output is not a directory: {output}")
    for asset in output.iterdir():
        known = asset.name in metadata or re.fullmatch(
            rf"(?:apache_ossie|{converter_wheel})-.+\.whl", asset.name
        )
        if asset.is_symlink() or not asset.is_file() or not known:
            raise ValueError(f"Output contains an unrelated file: {asset}")


def _publisher_revision(*, require_clean: bool) -> str:
    """Record the publisher commit and require committed build inputs in CI."""
    if require_clean:
        changes = subprocess.check_output(
            [
                "git",
                "status",
                "--porcelain",
                "--",
                "scripts/ossie-preview",
                ".github/workflows/ossie-preview.yml",
            ],
            cwd=WORKSPACE_ROOT,
            text=True,
        )
        if changes:
            raise ValueError(
                "Commit publisher changes before preparing a published preview"
            )
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=WORKSPACE_ROOT, text=True
    ).strip()


if __name__ == "__main__":
    main()
