"""Exercise the installed preview suite with real uv and converter processes."""

import os
import shutil
import subprocess
from pathlib import Path
from textwrap import dedent

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
INSTALLER = Path(__file__).with_name("install.sh")


@pytest.mark.integration
@pytest.mark.skipif(
    os.name == "nt", reason="The shell installer supports macOS and Linux"
)
def test_install_convert_and_uninstall(tmp_path: Path) -> None:
    # Use real tools without picking up an existing ossie-preview on PATH.
    tools = tmp_path / "tools"
    tools.mkdir()
    for name in ("uv", "git"):
        executable = shutil.which(name)
        assert executable is not None, f"{name} must be installed"
        (tools / name).symlink_to(executable)

    revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    commands = tmp_path / "commands"
    data = tmp_path / "data"
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("OSSIE_PREVIEW_")
        and key not in ("PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV")
    }
    environment.update(
        PATH=os.pathsep.join((str(tools), os.defpath)),
        XDG_DATA_HOME=str(data),
        UV_TOOL_BIN_DIR=str(commands),
        UV_PYTHON_DOWNLOADS="automatic",
        UV_PYTHON_PREFERENCE="only-managed",
        OSSIE_PREVIEW_HEX_REPO_URL=ROOT.as_uri(),
        OSSIE_PREVIEW_HEX_REV=revision,
    )

    def run(*args: str | Path) -> None:
        result = subprocess.run(
            [str(arg) for arg in args],
            cwd=tmp_path,
            env=environment,
            capture_output=True,
            text=True,
            timeout=900,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr

    dispatcher = commands / "ossie-preview"
    run("sh", INSTALLER)
    try:
        for converter in (
            "hex",
            "databricks",
            "dbt",
            "honeydew",
            "nvidia",
            "omni",
            "orionbelt",
            "wisdom",
        ):
            run(dispatcher, converter, "--help")

        source = tmp_path / "metric_view.yaml"
        source.write_text(
            dedent("""\
                version: '1.1'
                source: analytics.public.orders
                dimensions:
                  - name: order_id
                    expr: order_id
                measures:
                  - name: order_count
                    expr: COUNT(source.order_id)
                """),
            encoding="utf-8",
        )
        intermediate = tmp_path / "model.ossie.yaml"
        output = tmp_path / "hex"
        run(dispatcher, "databricks", "import", "-i", source, "-o", intermediate)
        run(dispatcher, "hex", "export", "-i", intermediate, "-o", output)

        resources = list(output.rglob("*.yml"))
        assert len(resources) == 1, resources
        model = yaml.safe_load(resources[0].read_text())
        assert model["id"] == "orders"
        assert model["base_sql_table"] == "analytics.public.orders"
        dimensions = {field["id"]: field for field in model["dimensions"]}
        assert dimensions["order_id"]["expr_sql"] == "order_id"
        measures = {field["id"]: field for field in model["measures"]}
        assert measures["order_count"]["func_sql"] == "COUNT(${order_id})"
    finally:
        run("sh", INSTALLER, "uninstall")
    assert not dispatcher.exists()
    assert not (data / "ossie-preview" / "bin").exists()
