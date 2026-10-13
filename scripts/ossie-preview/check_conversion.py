"""Exercise the installed converter in its private consumer Python environment."""

import importlib
import json
import subprocess
import sys
from pathlib import Path

import yaml

# The packaged entrypoint handles argv and exit status just like its console script.
_ENTRYPOINT = (
    "import importlib.metadata as m, sys; "
    "package = sys.argv.pop(1); "
    "entry = next(e for e in m.distribution(package).entry_points "
    "if e.group == 'console_scripts'); "
    "sys.argv[0] = entry.name; sys.exit(entry.load()())"
)

# Export command, input flag (None means positional), and optional reverse command.
_CLI = {
    "hex": ("export", "-i", None),
    "dbt": ("ossie-to-msi", "-i", "msi-to-ossie"),
    "cube": ("export", "-i", "import"),
    "holistics": ("to-aml", None, None),
    "honeydew": ("ossie-to-honeydew", "-i", "honeydew-to-ossie"),
    "microsoft": ("export", "-i", "import"),
    "nvidia": ("export", "-i", "import"),
    "omni": ("export", "-i", "import"),
    "orionbelt": ("ossie-to-obml", "-i", "obml-to-ossie"),
    "sigma": ("ossie-to-sigma", "-i", "sigma-to-ossie"),
    "snowflake": (None, "-i", None),
    "thoughtspot": ("to-tml", None, "to-ossie"),
    "wisdom": ("ossie-to-wisdom", "-i", "wisdom-to-ossie"),
}
_DIRECTORY_OUTPUT = {"hex", "cube", "holistics", "honeydew", "omni", "thoughtspot"}


def main() -> None:
    name, package, input_path, working_path = sys.argv[1:]
    document = Path(input_path)
    working = Path(working_path)
    if name == "gooddata":
        _gooddata(document)
    elif name == "ontology":
        _ontology()
    elif name == "wisdom-semantic-view":
        _semantic_view(package, document, working)
    else:
        _cli(name, package, document, working)


def _run(package: str, *args: str | Path) -> None:
    result = subprocess.run(
        [sys.executable, "-I", "-c", _ENTRYPOINT, package, *map(str, args)],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def _cli(name: str, package: str, document: Path, working: Path) -> None:
    command, input_flag, reverse = _CLI[name]
    output = working / ("converted" if name in _DIRECTORY_OUTPUT else "converted.yaml")
    arguments: list[str | Path] = []
    if command:
        arguments.append(command)
    if input_flag:
        arguments.append(input_flag)
    arguments.extend([document, "-o", output])
    if name == "holistics":
        arguments.extend(
            ["--sql-dialect", "SNOWFLAKE", "--data-source-name", "warehouse"]
        )
    _run(package, *arguments)
    files = sorted(output.rglob("*")) if output.is_dir() else [output]
    content = "\n".join(p.read_text(encoding="utf-8") for p in files if p.is_file())
    assert "orders" in content and "order_id" in content, content
    if name == "hex":
        model = yaml.safe_load(next(output.rglob("*.yml")).read_text())
        assert model["base_sql_table"] == "analytics.public.orders"
        assert model["measures"][0]["func_sql"] == "COUNT(${order_id})"
    if reverse:
        restored = working / "restored.ossie.yaml"
        inputs = list(output.glob("*.tml")) if name == "thoughtspot" else [output]
        flags = [input_flag] if input_flag else []
        _run(package, reverse, *flags, *inputs, "-o", restored)
        model = yaml.safe_load(restored.read_text())
        dataset = next(d for d in model["datasets"] if d["name"] == "orders")
        assert any(f["name"] == "order_id" for f in dataset["fields"])


def _gooddata(document: Path) -> None:
    export = importlib.import_module("ossie_gooddata.ossie_to_gooddata")
    restore = importlib.import_module("ossie_gooddata.gooddata_to_ossie")
    model = export.ossie_to_gooddata(yaml.safe_load(document.read_text()))
    assert model.ldm.datasets[0].id == "orders"
    restored = restore.gooddata_to_ossie(model)
    assert restored["datasets"][0]["source"] == "analytics.public.orders"
    assert restored["datasets"][0]["fields"][0]["name"] == "order_id"


def _ontology() -> None:
    api = importlib.import_module("ossie_ontology")
    spec = api.OssieSpec.model_validate(
        {"name": "smoke", "ontology": [{"concept": "Order", "type": "EntityType"}]}
    )
    model = api.SpecToOssieConverter().convert(spec)
    restored = api.OssieToSpecConverter.convert(model)
    assert restored.name == "smoke"
    assert restored.ontology[0].concept == "Order"


def _semantic_view(package: str, document: Path, working: Path) -> None:
    output = working / "wisdom.json"
    _run(package, "to-wisdom", document, "-o", output)
    assert "bookings" in json.dumps(json.loads(output.read_text()))
    restored = working / "semantic-view-restored.yaml"
    _run(package, "to-semantic-view", output, "-o", restored)
    table = yaml.safe_load(restored.read_text())["tables"][0]
    assert table["name"] == "bookings"
    assert table["dimensions"][0]["name"] == "booking_id"


if __name__ == "__main__":
    main()
