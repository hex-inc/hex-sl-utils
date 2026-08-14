from pathlib import Path

import pytest

from scripts.release import release_candidate, release_from_tag, workspace_releases


def write_package(packages_dir: Path, name: str, version: str) -> None:
    package_dir = packages_dir / name
    package_dir.mkdir()
    (package_dir / "pyproject.toml").write_text(
        f'[project]\nname = "{name}"\nversion = "{version}"\n'
    )


def test_workspace_releases_are_sorted_by_package_path(tmp_path: Path) -> None:
    write_package(tmp_path, "second-package", "2.0.0")
    write_package(tmp_path, "first-package", "1.0.0")

    assert [release.name for release in workspace_releases(tmp_path)] == [
        "first-package",
        "second-package",
    ]


def test_release_tag_must_match_package_name_and_version(tmp_path: Path) -> None:
    write_package(tmp_path, "example-package", "1.2.3")

    release = release_from_tag("example-package-v1.2.3", tmp_path)

    assert release.name == "example-package"
    assert release.version == "1.2.3"


def test_release_tag_rejects_mismatched_version(tmp_path: Path) -> None:
    write_package(tmp_path, "example-package", "1.2.3")

    with pytest.raises(ValueError, match="Invalid release tag"):
        release_from_tag("example-package-v1.2.4", tmp_path)


def test_release_tag_allows_prerelease(tmp_path: Path) -> None:
    write_package(tmp_path, "example-package", "1.2.3rc1")

    release = release_from_tag("example-package-v1.2.3rc1", tmp_path)

    assert release.version == "1.2.3rc1"


def test_release_tag_rejects_development_version(tmp_path: Path) -> None:
    write_package(tmp_path, "example-package", "1.2.3.dev0")

    with pytest.raises(ValueError, match="development version"):
        release_from_tag("example-package-v1.2.3.dev0", tmp_path)


def test_release_candidate_selects_one_non_development_version(
    tmp_path: Path,
) -> None:
    write_package(tmp_path, "example-package", "1.2.3")
    write_package(tmp_path, "other-package", "2.0.0.dev0")

    release = release_candidate(tmp_path)

    assert release.name == "example-package"
    assert release.version == "1.2.3"


def test_release_candidate_requires_a_non_development_version(
    tmp_path: Path,
) -> None:
    write_package(tmp_path, "example-package", "1.2.3.dev0")

    with pytest.raises(ValueError, match="found: none"):
        release_candidate(tmp_path)


def test_release_candidate_rejects_multiple_non_development_versions(
    tmp_path: Path,
) -> None:
    write_package(tmp_path, "first-package", "1.2.3")
    write_package(tmp_path, "second-package", "2.0.0")

    with pytest.raises(ValueError, match="Expected exactly one"):
        release_candidate(tmp_path)
