#!/usr/bin/env python3
"""Create or update calc SQL snapshot files from their test definitions."""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CALC_TEST_ROOT = PROJECT_ROOT / "packages" / "hex-sl-utils" / "tests" / "calc"
SNAPSHOT_DIR = CALC_TEST_ROOT / "compiler" / "snapshot" / "expressions"
MODULE_PREFIX = "compiler.snapshot.expressions"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail instead of writing when calc SQL snapshots are stale",
    )
    args = parser.parse_args()

    generated = _generate_snapshots()
    existing_paths = set(SNAPSHOT_DIR.glob("test_snapshot_*.sql"))
    generated_paths = set(generated)
    orphaned_paths = sorted(existing_paths - generated_paths)

    if args.check:
        missing_paths = sorted(path for path in generated_paths if not path.exists())
        stale_paths = sorted(
            path
            for path, content in generated.items()
            if path.exists() and path.read_text() != content
        )
        if missing_paths or stale_paths or orphaned_paths:
            details = _format_paths("Missing", missing_paths)
            details += _format_paths("Stale", stale_paths)
            details += _format_paths("Orphaned", orphaned_paths)
            raise SystemExit(
                "Calc SQL snapshots are not current:\n"
                f"{details}"
                "Run `devbox run build:calc-sql-snapshots`."
            )
        print(f"All {len(generated)} calc SQL snapshots are current.")
        return

    changed_paths: list[Path] = []
    for path, content in sorted(generated.items()):
        if path.exists() and path.read_text() == content:
            continue
        path.write_text(content)
        changed_paths.append(path)
        print(f"Wrote {path.relative_to(PROJECT_ROOT)}")

    if orphaned_paths:
        details = _format_paths("Orphaned", orphaned_paths)
        raise SystemExit(
            "Calc SQL snapshots exist without matching test modules:\n"
            f"{details}"
            "Remove the orphaned files explicitly."
        )

    if not changed_paths:
        print(f"All {len(generated)} calc SQL snapshots are already current.")


def _generate_snapshots() -> dict[Path, str]:
    sys.path.insert(0, str(CALC_TEST_ROOT))
    sys.path.insert(0, str(PROJECT_ROOT / "packages" / "hex-sl-utils" / "tests"))
    snapshot_base = importlib.import_module("compiler.snapshot.snapshot_base")
    snapshot_test_base = snapshot_base.SnapshotTestBase

    generated: dict[Path, str] = {}
    for test_path in sorted(SNAPSHOT_DIR.glob("test_snapshot_*.py")):
        module = importlib.import_module(f"{MODULE_PREFIX}.{test_path.stem}")
        snapshot_test = getattr(module, "SnapshotTest", None)
        if not isinstance(snapshot_test, type) or not issubclass(
            snapshot_test, snapshot_test_base
        ):
            raise TypeError(f"{test_path} does not define a SnapshotTest subclass")
        generated[test_path.with_suffix(".sql")] = snapshot_test.render_sql_snapshot()

    if not generated:
        raise RuntimeError(f"No snapshot tests found in {SNAPSHOT_DIR}")
    return generated


def _format_paths(label: str, paths: list[Path]) -> str:
    if not paths:
        return ""
    formatted = "\n".join(f"  - {path.relative_to(PROJECT_ROOT)}" for path in paths)
    return f"{label}:\n{formatted}\n"


if __name__ == "__main__":
    main()
