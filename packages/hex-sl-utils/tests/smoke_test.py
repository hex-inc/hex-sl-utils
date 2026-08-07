"""Smoke test for installed hex-sl-utils distributions."""

from pathlib import Path

import hex_sl_utils

assert Path(hex_sl_utils.__file__).name == "__init__.py"
