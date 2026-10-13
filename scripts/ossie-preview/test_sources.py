"""Check shared and per-converter source pins without downloading tooling."""

import pytest
from build_wheels import load_converter_source
from constants import HEX_PREVIEW


@pytest.mark.parametrize("override", [False, True], ids=["shared", "override"])
def test_converter_source(tmp_path, monkeypatch, override):
    shared = "a" * 40
    specific = "b" * 40
    sources = tmp_path / "sources.toml"
    sources.write_text(
        f'commit = "{shared}"\n[converters.hex]\ndirectory = "converters/hex"\n'
        + (f'commit = "{specific}"\n' if override else ""),
        encoding="utf-8",
    )
    monkeypatch.setattr("build_wheels.SOURCES_FILE", sources)

    source = load_converter_source(HEX_PREVIEW)

    assert source.commit == (specific if override else shared)
    assert source.directory == "converters/hex"


def test_requires_immutable_source(tmp_path, monkeypatch):
    sources = tmp_path / "sources.toml"
    sources.write_text(
        'commit = "main"\n[converters.hex]\ndirectory = "converters/hex"\n',
        encoding="utf-8",
    )
    monkeypatch.setattr("build_wheels.SOURCES_FILE", sources)

    with pytest.raises(ValueError, match="full Git commit"):
        load_converter_source(HEX_PREVIEW)
