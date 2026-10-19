"""Require release sources to share one pinned upstream checkout."""

import tomllib
from pathlib import Path

import build_wheels
import pytest


@pytest.fixture
def bundle(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    upstream = tmp_path / "upstream"
    sources = {
        "apache-ossie": "ossie/python",
        "example-one": "one",
        "example-two": "two",
    }
    for name, relative in sources.items():
        package = upstream / relative
        package.mkdir(parents=True)
        metadata = f'[project]\nname = "{name}"\n'
        if name != "apache-ossie":
            metadata += (
                '[tool.uv.sources]\napache-ossie = { path = "../ossie/python" }\n'
            )
        (package / "pyproject.toml").write_text(metadata)
    project = tmp_path / "bundle"
    project.mkdir()
    (project / "pyproject.toml").write_text(
        "[tool.uv.sources]\n"
        + "".join(
            f'{name} = {{ path = "../upstream/{relative}" }}\n'
            for name, relative in sources.items()
        )
    )
    monkeypatch.setattr(build_wheels, "BUNDLE_PROJECT", project)
    monkeypatch.setattr(build_wheels, "CONVERTER_SOURCE", upstream)
    monkeypatch.setattr(build_wheels, "RELEASE_PACKAGES", tuple(sources))
    return project


def test_sources_share_the_pinned_submodule(bundle: Path) -> None:
    assert build_wheels.load_package_sources() == {
        "apache-ossie": bundle.parent / "upstream/ossie/python",
        "example-one": bundle.parent / "upstream/one",
        "example-two": bundle.parent / "upstream/two",
    }


@pytest.mark.parametrize(
    "source",
    [
        '{ git = "https://github.com/apache/ossie.git" }',
        '{ path = "../other-checkout" }',
    ],
)
def test_sources_must_be_inside_submodule(bundle: Path, source: str) -> None:
    pyproject = bundle / "pyproject.toml"
    pyproject.write_text(
        pyproject.read_text().replace('{ path = "../upstream/ossie/python" }', source)
    )
    with pytest.raises(ValueError, match="inside.*submodule"):
        build_wheels.load_package_sources()


def test_converters_cannot_use_different_ossie_sources(bundle: Path) -> None:
    converter = bundle.parent / "upstream/two/pyproject.toml"
    converter.write_text(converter.read_text().replace("../ossie/python", "../other"))
    with pytest.raises(ValueError, match="shared Apache Ossie source"):
        build_wheels.load_package_sources()


def test_bundle_package_identity_must_match_source(bundle: Path) -> None:
    converter = bundle.parent / "upstream/two/pyproject.toml"
    converter.write_text(converter.read_text().replace("example-two", "other"))
    with pytest.raises(ValueError, match="does not declare package example-two"):
        build_wheels.load_package_sources()


def test_wheels_include_their_own_repository_notices(
    bundle: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    upstream = bundle.parent / "upstream"
    notices = ("LICENSE", "NOTICE")
    for checkout, label in ((upstream, "converters"), (upstream / "ossie", "sdk")):
        for notice in notices:
            (checkout / notice).write_text(f"{label} {notice}")
    included: dict[str, dict[str, str]] = {}

    def build_wheel(package: Path, output: Path) -> None:
        metadata = tomllib.loads((package / "pyproject.toml").read_text())
        name = metadata["project"]["name"]
        included[name] = {notice: (package / notice).read_text() for notice in notices}
        (output / f"{name.replace('-', '_')}-0.0.0-py3-none-any.whl").touch()

    monkeypatch.setattr(build_wheels, "_build_wheel", build_wheel)
    build_wheels.build_wheels(tmp_path / "wheels")
    assert included == {
        "apache-ossie": {notice: f"sdk {notice}" for notice in notices},
        "example-one": {notice: f"converters {notice}" for notice in notices},
        "example-two": {notice: f"converters {notice}" for notice in notices},
    }
