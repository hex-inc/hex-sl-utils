from pathlib import Path

import hex_sl_utils


def test_package_is_importable() -> None:
    assert Path(hex_sl_utils.__file__).name == "__init__.py"
