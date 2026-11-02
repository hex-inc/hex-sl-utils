"""Select a dated preview release when its committed build inputs change."""

import argparse
import json
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from constants import WORKSPACE_ROOT

TAG_PREFIX = "ossie-preview/"
# Tests, documentation, and workflow/release planning do not change the payload.
RELEASE_INPUTS = (
    "external/apache-ossie-converters",
    ".gitmodules",
    "scripts/ossie-preview/bundle",
    "scripts/ossie-preview/build_wheels.py",
    "scripts/ossie-preview/constants.py",
    "scripts/ossie-preview/main.py",
    "scripts/ossie-preview/release_artifacts.py",
)


def next_release_id(tags: list[str], date: str) -> str:
    """Use the UTC date, incrementing the suffix after any reserved version."""
    base = f"v{date}"
    pattern = re.compile(rf"{re.escape(TAG_PREFIX + base)}(?:-([2-9]|[1-9][0-9]+))?")
    versions = [int(match[1] or 1) for tag in tags if (match := pattern.fullmatch(tag))]
    return f"{base}-{max(versions) + 1}" if versions else base


def release_inputs_changed(previous: str) -> bool:
    """Compare inputs with a published tag; never release a superseded commit."""
    # The tag's target_commitish may be a moving branch, so compare the tag itself.
    revision = _git("rev-parse", "--verify", f"refs/tags/{previous}^{{commit}}")
    if revision == _git("rev-parse", "HEAD"):
        return False
    if _git_status("merge-base", "--is-ancestor", "HEAD", revision) == 0:
        return False
    return _git_status("diff", "--quiet", revision, "HEAD", "--", *RELEASE_INPUTS) == 1


def plan_release(*, publish: bool) -> tuple[str, bool]:
    """Keep PR builds private and skip unchanged published previews."""
    if not publish:
        return f"candidate-{_git('rev-parse', 'HEAD')}", False
    pages = json.loads(
        subprocess.check_output(
            ["gh", "api", "repos/{owner}/{repo}/releases", "--paginate", "--slurp"],
            cwd=WORKSPACE_ROOT,
            text=True,
        )
    )
    releases = [
        release
        for page in pages
        for release in page
        if release["tag_name"].startswith(TAG_PREFIX)
    ]
    published = [release for release in releases if not release["draft"]]
    if published:
        latest = max(published, key=lambda release: release["published_at"])
        if not release_inputs_changed(latest["tag_name"]):
            print(f"Preview inputs are already published in {latest['tag_name']}")
            return "", False
    tags = _git("tag", "--list", f"{TAG_PREFIX}*").splitlines()
    tags.extend(release["tag_name"] for release in releases)
    return next_release_id(tags, datetime.now(UTC).strftime("%Y.%m.%d")), True


def _git(*arguments: str) -> str:
    return subprocess.check_output(
        ["git", *arguments], cwd=WORKSPACE_ROOT, text=True
    ).strip()


def _git_status(*arguments: str) -> int:
    result = subprocess.run(["git", *arguments], cwd=WORKSPACE_ROOT, check=False)
    if result.returncode not in (0, 1):
        result.check_returncode()
    return result.returncode


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--github-output", required=True, type=Path)
    args = parser.parse_args()
    release_id, publish = plan_release(publish=args.publish)
    with args.github_output.open("a") as output:
        output.write(f"release_id={release_id}\npublish={str(publish).lower()}\n")
    if release_id:
        print(f"Selected preview {release_id} (publish={publish})")


if __name__ == "__main__":
    main()
