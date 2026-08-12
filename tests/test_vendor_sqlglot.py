"""Tests for the SQLGlot vendoring workflow."""

import importlib.util
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
VENDOR_SCRIPT = PROJECT_ROOT / "scripts" / "vendoring" / "vendor_sqlglot.py"


def test_packaged_vendored_licenses_matches_top_level_file() -> None:
    packaged_licenses = PROJECT_ROOT / "packages" / "hex-sl-utils" / "VENDORED_LICENSES"

    assert (
        packaged_licenses.read_bytes()
        == (PROJECT_ROOT / "VENDORED_LICENSES").read_bytes()
    )


def load_vendor_script():
    spec = importlib.util.spec_from_file_location("vendor_sqlglot", VENDOR_SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_download_failure_preserves_existing_vendor_tree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    vendor_sqlglot = load_vendor_script()
    vendor_dir = tmp_path / "_vendor" / "sqlglot"
    existing_file = vendor_dir / "existing.py"
    existing_file.parent.mkdir(parents=True)
    existing_file.write_text("# committed artifact\n")

    monkeypatch.setattr(vendor_sqlglot, "VENDOR_DIR", vendor_dir)

    def fail_download(version: str) -> Path:
        raise RuntimeError("simulated download failure")

    monkeypatch.setattr(vendor_sqlglot, "download_sqlglot", fail_download)

    with pytest.raises(RuntimeError, match="simulated download failure"):
        vendor_sqlglot.main()

    assert existing_file.read_text() == "# committed artifact\n"
