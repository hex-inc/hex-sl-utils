"""Regenerate vendored SQLGlot and fail if the committed artifact changes."""

import subprocess
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
vendor_script = project_root / "scripts" / "vendoring" / "vendor_sqlglot.py"
vendor_dir = (
    project_root
    / "packages"
    / "hex-sl-utils"
    / "src"
    / "hex_sl_utils"
    / "_vendor"
    / "sqlglot"
)

generated = subprocess.run(
    [sys.executable, str(vendor_script)], cwd=project_root, check=False
)
if generated.returncode != 0:
    sys.exit(generated.returncode)

relative_vendor_dir = vendor_dir.relative_to(project_root)
status = subprocess.run(
    [
        "git",
        "status",
        "--short",
        "--untracked-files=all",
        "--",
        str(relative_vendor_dir),
    ],
    cwd=project_root,
    capture_output=True,
    text=True,
    check=False,
)
if status.returncode != 0:
    print(status.stderr, file=sys.stderr)
    sys.exit(status.returncode)

if status.stdout:
    print("Vendored SQLGlot is not reproducible:")
    print(status.stdout, end="")
    sys.exit(1)

print("Vendored SQLGlot matches the generated artifact.")
