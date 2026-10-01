"""Exercise installed distributions without importing the source checkout."""

import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

import yaml

from ossie_hex import convert_ossie_to_hex


def main() -> None:
    """Check the public API and installed command."""
    with TemporaryDirectory() as directory:
        root = Path(directory)
        document = root / "model.yaml"
        document.write_text(
            "version: '0.2.0.dev0'\n"
            "name: smoke\n"
            "datasets:\n"
            "  - name: orders\n"
            "    source: orders\n"
            "    fields:\n"
            "      - name: id\n"
            "        datatype: Integer\n"
            "        expression:\n"
            "          dialects:\n"
            "            - dialect: ANSI_SQL\n"
            "              expression: id\n",
            encoding="utf-8",
        )
        project, problems = convert_ossie_to_hex(document, None, dialect=None)
        assert project is not None, problems
        assert not [p for p in problems if p.severity in ("error", "fatal")], problems
        output = root / "output"
        subprocess.run(
            ["ossie-hex", "export", "-i", str(document), "-o", str(output)],
            check=True,
            cwd=root,
        )
        resources = list(output.rglob("*.yml"))
        assert len(resources) == 1, resources
        assert yaml.safe_load(resources[0].read_text())["id"] == "orders"


if __name__ == "__main__":
    main()
