"""Shared paths and sources for the Ossie preview workflow."""

import tomllib
from pathlib import Path

SCRIPTS_DIRECTORY = Path(__file__).resolve().parent
WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
CONVERTER_SOURCE = WORKSPACE_ROOT / "external" / "apache-ossie-converters"
BUNDLE_PROJECT = SCRIPTS_DIRECTORY / "bundle"
RELEASE_PACKAGES: tuple[str, ...] = tuple(
    tomllib.loads((BUNDLE_PROJECT / "pyproject.toml").read_text())["project"][
        "dependencies"
    ]
)
CONVERTER_REPOSITORY = "https://github.com/hex-inc/apache-ossie-converters"
RELEASE_REPOSITORY = "hex-inc/hex-sl-utils"

PYTHON_VERSION = "3.12"
DEFAULT_ASSETS_DIRECTORY = WORKSPACE_ROOT / "dist" / "ossie-preview"
