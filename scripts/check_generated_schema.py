"""Regenerate schema artifacts and fail when checked-in files are stale."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_FILES = (
    ROOT / "packages" / "hex-sl-utils" / "src" / "hex_sl_utils" / "schema_files"
)


def main() -> None:
    """Regenerate schemas and compare them with their previous contents."""
    paths = sorted(path for path in SCHEMA_FILES.rglob("*") if path.is_file())
    before = {path: path.read_bytes() for path in paths}

    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "schema" / "generate_schema.py")],
        cwd=ROOT,
        check=True,
    )

    generated_paths = sorted(path for path in SCHEMA_FILES.rglob("*") if path.is_file())
    changed = [
        path.relative_to(ROOT)
        for path in sorted(set(paths) | set(generated_paths))
        if before.get(path) != (path.read_bytes() if path.exists() else None)
    ]
    if changed:
        formatted = "\n".join(f"  - {path}" for path in changed)
        raise SystemExit(f"Generated schema artifacts are stale:\n{formatted}")


if __name__ == "__main__":
    main()
