"""Validate a package-scoped release tag for the publishing workflow."""

from __future__ import annotations

import argparse
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from packaging.version import InvalidVersion, Version

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = ROOT / "packages"


@dataclass(frozen=True)
class PackageRelease:
    """Release metadata read from a workspace member."""

    name: str
    version: str

    @property
    def tag(self) -> str:
        """Return the only release tag valid for this package version."""
        return f"{self.name}-v{self.version}"


def workspace_releases(packages_dir: Path = PACKAGES) -> list[PackageRelease]:
    """Read statically versioned publishable packages in stable path order."""
    releases: list[PackageRelease] = []
    for pyproject in sorted(packages_dir.glob("*/pyproject.toml")):
        data: dict[str, Any] = tomllib.loads(pyproject.read_text())
        project = data["project"]
        releases.append(PackageRelease(project["name"], project["version"]))
    return releases


def validated_release(release: PackageRelease) -> PackageRelease:
    """Validate that package metadata identifies a publishable release."""
    try:
        version = Version(release.version)
    except InvalidVersion as error:
        raise ValueError(
            f"Package {release.name!r} has invalid version {release.version!r}"
        ) from error

    if version.is_devrelease:
        raise ValueError(f"Refusing to publish development version {release.version!r}")
    return release


def release_from_tag(tag: str, packages_dir: Path = PACKAGES) -> PackageRelease:
    """Resolve and validate the one workspace package identified by a tag."""
    releases = workspace_releases(packages_dir)
    matches = [release for release in releases if release.tag == tag]
    if len(matches) != 1:
        expected = ", ".join(release.tag for release in releases)
        raise ValueError(f"Invalid release tag {tag!r}; expected one of: {expected}")

    return validated_release(matches[0])


def release_candidate(packages_dir: Path = PACKAGES) -> PackageRelease:
    """Find the one publishable package prepared by a release pull request."""
    candidates: list[PackageRelease] = []
    for release in workspace_releases(packages_dir):
        try:
            version = Version(release.version)
        except InvalidVersion as error:
            raise ValueError(
                f"Package {release.name!r} has invalid version {release.version!r}"
            ) from error
        if not version.is_devrelease:
            candidates.append(release)

    if len(candidates) != 1:
        found = ", ".join(candidate.tag for candidate in candidates) or "none"
        raise ValueError(
            f"Expected exactly one non-development release candidate; found: {found}"
        )
    return candidates[0]


def main() -> None:
    """Validate a tag and optionally expose its metadata as GitHub outputs."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "tag", nargs="?", help="Git tag in <distribution>-v<version> form"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="validate the one non-development package prepared for release",
    )
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()

    if args.dry_run:
        if args.tag is not None:
            parser.error("tag cannot be used with --dry-run")
        release = release_candidate()
        print(f"Validated release candidate: {release.name} {release.version}")
    else:
        if args.tag is None:
            parser.error("tag is required unless --dry-run is used")
        release = release_from_tag(args.tag)
        print(f"Validated release: {release.name} {release.version}")

    if args.github_output is not None:
        with args.github_output.open("a") as output:
            output.write(f"package={release.name}\n")
            output.write(f"version={release.version}\n")


if __name__ == "__main__":
    main()
