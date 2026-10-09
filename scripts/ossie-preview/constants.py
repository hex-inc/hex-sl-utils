"""Shared paths and sources for the Ossie preview workflow."""

from pathlib import Path

SCRIPTS_DIRECTORY = Path(__file__).resolve().parent
WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
OSSIE_HEX_PACKAGE = WORKSPACE_ROOT / "packages" / "ossie-hex"
APACHE_OSSIE_SOURCE = "https://github.com/apache/ossie.git"
RELEASE_REPOSITORY = "hex-inc/hex-sl-utils"

PYTHON_VERSION = "3.12"
DEPENDENCY_LOCK = SCRIPTS_DIRECTORY / "requirements.lock"
DEFAULT_ASSETS_DIRECTORY = WORKSPACE_ROOT / "dist" / "ossie-preview"
