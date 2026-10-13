"""Shared paths and sources for the Ossie preview workflow."""

import tomllib
from dataclasses import dataclass
from pathlib import Path

SCRIPTS_DIRECTORY = Path(__file__).resolve().parent
WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
SOURCES_FILE = SCRIPTS_DIRECTORY / "sources.toml"
APACHE_OSSIE_SOURCE = "https://github.com/apache/ossie.git"
RELEASE_REPOSITORY = "hex-inc/hex-sl-utils"

PYTHON_VERSION = "3.12"


@dataclass(frozen=True)
class PreviewConverter:
    name: str
    package_name: str

    @property
    def tag_prefix(self) -> str:
        return "ossie-preview" if self.name == "hex" else f"ossie-preview/{self.name}"

    @property
    def assets_directory(self) -> Path:
        suffix = "" if self.name == "hex" else f"-{self.name}"
        return WORKSPACE_ROOT / "dist" / f"ossie-preview{suffix}"


with SOURCES_FILE.open("rb") as source_file:
    _sources = tomllib.load(source_file)["converters"]
CONVERTERS = {
    name: PreviewConverter(
        name=name,
        package_name=source["package"],
    )
    for name, source in _sources.items()
}
HEX_PREVIEW = CONVERTERS["hex"]
