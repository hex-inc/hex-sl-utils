"""Exercise preview deduplication and version allocation against Git history."""

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import plan_release
import pytest


@pytest.mark.parametrize(
    ("tags", "expected"),
    [
        ([], "v2026.11.02"),
        (["ossie-preview/v2026.11.01"], "v2026.11.02"),
        (["ossie-preview/v2026.11.02"], "v2026.11.02-2"),
        (["ossie-preview/v2026.11.02-2"], "v2026.11.02-3"),
        (
            ["ossie-preview/v2026.11.02-9", "ossie-preview/v2026.11.02-10"],
            "v2026.11.02-11",
        ),
        (["other/v2026.11.02", "ossie-preview/v2026.11.02-extra"], "v2026.11.02"),
    ],
)
def test_date_versions(tags: list[str], expected: str) -> None:
    assert plan_release.next_release_id(tags, "2026.11.02") == expected


@pytest.fixture
def history(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(plan_release, "WORKSPACE_ROOT", tmp_path)
    _git(tmp_path, "init", "--initial-branch=main")
    _git(tmp_path, "config", "user.name", "Preview Test")
    _git(tmp_path, "config", "user.email", "preview@example.com")
    _commit_file(tmp_path, "scripts/ossie-preview/bundle/uv.lock", "original")
    _git(tmp_path, "tag", "ossie-preview/v2026.10.21")
    return tmp_path


def test_retry_and_non_payload_changes_do_not_release(history: Path) -> None:
    tag = "ossie-preview/v2026.10.21"
    assert not plan_release.release_inputs_changed(tag)
    for path in (
        "scripts/ossie-preview/README.md",
        "scripts/ossie-preview/test_installation.py",
        "scripts/ossie-preview/fixtures/model.ossie.yaml",
        "scripts/ossie-preview/plan_release.py",
        ".github/workflows/ossie-preview.yml",
        "packages/unrelated.py",
    ):
        _commit_file(history, path, "changed")
        assert not plan_release.release_inputs_changed(tag)


def test_reverted_inputs_do_not_release(history: Path) -> None:
    _commit_file(history, "scripts/ossie-preview/bundle/uv.lock", "changed")
    _commit_file(history, "scripts/ossie-preview/bundle/uv.lock", "original")
    assert not plan_release.release_inputs_changed("ossie-preview/v2026.10.21")


@pytest.mark.parametrize(
    "path",
    [
        "scripts/ossie-preview/bundle/uv.lock",
        "scripts/ossie-preview/bundle/pyproject.toml",
        "scripts/ossie-preview/build_wheels.py",
        "scripts/ossie-preview/constants.py",
        "scripts/ossie-preview/main.py",
        "scripts/ossie-preview/release_artifacts.py",
        ".gitmodules",
    ],
)
def test_changed_build_inputs_release(history: Path, path: str) -> None:
    _commit_file(history, path, "changed")
    assert plan_release.release_inputs_changed("ossie-preview/v2026.10.21")


def test_changed_submodule_pin_releases(history: Path) -> None:
    revision = _git(history, "rev-parse", "HEAD")
    _git(
        history,
        "update-index",
        "--add",
        "--cacheinfo",
        f"160000,{revision},external/apache-ossie-converters",
    )
    _git(history, "commit", "-m", "Pin converters")
    assert plan_release.release_inputs_changed("ossie-preview/v2026.10.21")


def test_a_superseded_run_does_not_publish_older_sources(history: Path) -> None:
    _commit_file(history, "scripts/ossie-preview/bundle/uv.lock", "newer")
    _git(history, "tag", "ossie-preview/v2026.11.02")
    _git(history, "checkout", "--detach", "ossie-preview/v2026.10.21")
    assert not plan_release.release_inputs_changed("ossie-preview/v2026.11.02")


def test_missing_published_tag_fails_instead_of_releasing(history: Path) -> None:
    with pytest.raises(subprocess.CalledProcessError):
        plan_release.release_inputs_changed("ossie-preview/missing")


@pytest.fixture
def github_releases(
    monkeypatch: pytest.MonkeyPatch,
) -> list[dict[str, object]]:
    releases: list[dict[str, object]] = []
    check_output = subprocess.check_output

    def fake_output(command: list[str], *, cwd: Path, text: bool) -> str:
        if command[0] == "gh":
            return json.dumps([releases[:2], releases[2:]])
        return check_output(command, cwd=cwd, text=text)

    monkeypatch.setattr(subprocess, "check_output", fake_output)
    return releases


def test_first_preview_is_published(
    history: Path, github_releases: list[dict[str, object]]
) -> None:
    today = datetime.now(UTC).strftime("%Y.%m.%d")
    assert plan_release.plan_release(publish=True) == (f"v{today}", True)


def test_plan_uses_latest_publication_and_reserves_drafts(
    history: Path, github_releases: list[dict[str, object]]
) -> None:
    today = datetime.now(UTC).strftime("%Y.%m.%d")
    old = "ossie-preview/v2026.10.21"
    newest = "ossie-preview/v2026.10.22"
    # Publication time, not the API's creation order, identifies the baseline.
    github_releases.extend(
        [
            {"tag_name": old, "draft": False, "published_at": "2026-10-21T00:00:00Z"},
            {
                "tag_name": newest,
                "draft": False,
                "published_at": "2026-10-22T00:00:00Z",
            },
            {
                "tag_name": f"ossie-preview/v{today}",
                "draft": True,
                "published_at": None,
            },
            {"tag_name": "unrelated/v99", "draft": False, "published_at": "2099"},
        ]
    )
    _commit_file(history, "scripts/ossie-preview/bundle/uv.lock", "updated")
    _git(history, "tag", newest)
    assert plan_release.plan_release(publish=True) == ("", False)
    _commit_file(history, "scripts/ossie-preview/bundle/uv.lock", "next")
    _git(history, "tag", f"ossie-preview/v{today}-2")
    assert plan_release.plan_release(publish=True) == (f"v{today}-3", True)


def test_candidate_does_not_query_releases(history: Path) -> None:
    assert plan_release.plan_release(publish=False) == (
        f"candidate-{_git(history, 'rev-parse', 'HEAD')}",
        False,
    )


def _git(directory: Path, *arguments: str) -> str:
    return subprocess.check_output(
        ["git", *arguments], cwd=directory, text=True
    ).strip()


def _commit_file(directory: Path, path: str, contents: str) -> None:
    file = directory / path
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(contents)
    _git(directory, "add", "--", path)
    _git(directory, "commit", "-m", f"Update {path}")
