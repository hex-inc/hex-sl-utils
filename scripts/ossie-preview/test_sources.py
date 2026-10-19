"""Check that Apache Ossie follows the converter's declared source."""

from pathlib import Path

import build_wheels
import pytest


@pytest.fixture
def converter(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    package = tmp_path / "converters" / "hex"
    package.mkdir(parents=True)
    monkeypatch.setattr(build_wheels, "OSSIE_HEX_PACKAGE", package)
    monkeypatch.setattr(build_wheels, "CONVERTER_SOURCE", tmp_path)
    return package


def test_apache_source_follows_converter(converter: Path) -> None:
    (converter / "pyproject.toml").write_text(
        '[tool.uv.sources]\napache-ossie = { path = "../../python" }\n'
    )
    assert build_wheels.load_apache_ossie_package() == converter.parents[1] / "python"


@pytest.mark.parametrize(
    "source",
    [
        '{ git = "https://github.com/apache/ossie.git" }',
        '{ path = "../../../other-checkout" }',
    ],
)
def test_apache_source_must_be_inside_submodule(converter: Path, source: str) -> None:
    (converter / "pyproject.toml").write_text(
        f"[tool.uv.sources]\napache-ossie = {source}\n"
    )
    with pytest.raises(ValueError, match="inside.*submodule"):
        build_wheels.load_apache_ossie_package()
