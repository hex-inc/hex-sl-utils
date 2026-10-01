"""Install real release wheels without Git or ambient Python and convert a model."""

import hashlib
import os
import shutil
import subprocess
import sys
import threading
import zipfile
from collections.abc import Iterator
from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from textwrap import dedent

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
BUILDER = Path(__file__).with_name("preview.py")


@pytest.fixture(scope="module")
def assets(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Use CI's exact release payload, or build a real local candidate."""
    if supplied := os.environ.get("OSSIE_PREVIEW_ASSETS"):
        directory = Path(supplied).resolve()
    else:
        directory = tmp_path_factory.mktemp("preview-build") / "assets"
        subprocess.run(
            [
                sys.executable,
                str(BUILDER),
                "build",
                "test",
                "--out-dir",
                str(directory),
            ],
            cwd=ROOT,
            check=True,
            timeout=300,
        )
    for line in (directory / "SHA256SUMS").read_text().splitlines():
        digest, name = line.split("  ", 1)
        assert hashlib.sha256((directory / name).read_bytes()).hexdigest() == digest
    return directory


@contextmanager
def serve(directory: Path) -> Iterator[str]:
    """Serve the release assets over actual HTTP, as the release CDN would."""
    handler = partial(SimpleHTTPRequestHandler, directory=str(directory))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def consumer_environment(directory: Path) -> dict[str, str]:
    """Expose only the real uv executable, with private Python and package storage."""
    executable = shutil.which("uv")
    assert executable is not None, "uv must be installed to run the integration test"
    tools = directory / "tools"
    tools.mkdir()
    shutil.copy2(executable, tools / Path(executable).name)
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("UV_")
        and key not in ("PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV")
    }
    environment.update(
        PATH=str(tools),
        UV_NO_CONFIG="1",
        UV_CACHE_DIR=str(directory / "cache"),
        UV_PYTHON_INSTALL_DIR=str(directory / "python"),
        UV_PYTHON_DOWNLOADS="automatic",
        PYTHONNOUSERSITE="1",
    )
    assert shutil.which("git", path=environment["PATH"]) is None
    assert shutil.which("python", path=environment["PATH"]) is None
    return environment


def run(
    directory: Path, environment: dict[str, str], *args: str | Path
) -> subprocess.CompletedProcess[str]:
    """Run customer commands outside the checkout and retain errors for assertions."""
    return subprocess.run(
        [str(arg) for arg in args],
        cwd=directory,
        env=environment,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )


def assert_success(result: subprocess.CompletedProcess[str]) -> None:
    assert result.returncode == 0, result.stdout + result.stderr


def requirements_at(directory: Path, base: str) -> None:
    """Point the preview's simple index at the real local HTTP server."""
    path = directory / "requirements.txt"
    text = path.read_text()
    release_index = next(
        line.removeprefix("--extra-index-url ")
        for line in text.splitlines()
        if line.startswith("--extra-index-url ")
    )
    assert release_index.startswith(
        "https://hex-internal-pypi-index.hex.tech/ossie-preview/"
    )
    path.write_text(text.replace(release_index, f"{base}/simple/"), encoding="utf-8")


def test_release_payload(assets: Path) -> None:
    wheels = list(assets.glob("*.whl"))
    assert len(wheels) == 2
    for wheel in wheels:
        assert wheel.name.endswith("-py3-none-any.whl")
        with zipfile.ZipFile(wheel) as package:
            assert any(
                name.endswith("/licenses/LICENSE") for name in package.namelist()
            )
            assert any(name.endswith("/licenses/NOTICE") for name in package.namelist())
    sources = (assets / "SOURCES.txt").read_text()
    assert "https://github.com/apache/ossie " in sources
    assert "hex-inc/apache-ossie" not in sources
    requirements = (assets / "requirements.txt").read_text()
    assert "hex-sl-utils==0.2.0" in requirements
    assert "--index-url https://pypi.org/simple" in requirements
    assert "--extra-index-url https://hex-internal-pypi-index.hex.tech/" in requirements
    assert "git+" not in requirements
    assert "file:" not in requirements


@pytest.mark.integration
def test_install_and_convert(assets: Path, tmp_path: Path) -> None:
    environment = consumer_environment(tmp_path)
    venv = tmp_path / "venv"
    assert_success(
        run(
            tmp_path,
            environment,
            "uv",
            "venv",
            "--managed-python",
            "--python",
            "3.12",
            venv,
        )
    )
    served = tmp_path / "release"
    shutil.copytree(assets, served)
    with serve(served) as base:
        requirements_at(served, base)
        assert_success(
            run(
                tmp_path,
                environment,
                "uv",
                "pip",
                "install",
                "--python",
                venv,
                "--require-hashes",
                "--only-binary",
                ":all:",
                "-r",
                f"{base}/requirements.txt",
            )
        )
    python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    assert_success(
        run(
            tmp_path,
            environment,
            python,
            "-I",
            "-c",
            "import importlib.metadata as m, pathlib, sys; "
            "assert m.version('hex-sl-utils') == '0.2.0'; "
            "assert all(m.distribution(n).read_text('direct_url.json') is None "
            "for n in ('ossie-hex', 'apache-ossie', 'hex-sl-utils')); "
            f"assert pathlib.Path(sys.base_prefix).is_relative_to(pathlib.Path({str(tmp_path / 'python')!r}))",
        )
    )
    document = tmp_path / "model.yaml"
    document.write_text(
        dedent("""\
        version: '0.2.0.dev0'
        name: smoke
        datasets:
          - name: orders
            source: analytics.public.orders
            fields:
              - name: order_id
                datatype: Integer
                expression:
                  dialects:
                    - dialect: ANSI_SQL
                      expression: order_id
        metrics:
          - name: order_count
            datatype: Integer
            expression:
              dialects:
                - dialect: ANSI_SQL
                  expression: COUNT(orders.order_id)
        """),
        encoding="utf-8",
    )
    output = tmp_path / "hex"
    assert_success(
        run(
            tmp_path,
            environment,
            python,
            "-I",
            "-m",
            "ossie_hex.cli",
            "export",
            "-i",
            document,
            "-o",
            output,
        )
    )
    resources = list(output.rglob("*.yml"))
    assert len(resources) == 1
    model = yaml.safe_load(resources[0].read_text())
    assert model["id"] == "orders"
    assert model["base_sql_table"] == "analytics.public.orders"
    assert model["dimensions"][0]["expr_sql"] == "order_id"
    assert model["measures"][0]["func_sql"] == "COUNT(${order_id})"


@pytest.mark.integration
def test_modified_wheel_is_rejected(assets: Path, tmp_path: Path) -> None:
    environment = consumer_environment(tmp_path)
    venv = tmp_path / "venv"
    assert_success(
        run(
            tmp_path,
            environment,
            "uv",
            "venv",
            "--managed-python",
            "--python",
            "3.12",
            venv,
        )
    )
    served = tmp_path / "release"
    shutil.copytree(assets, served)
    wheel = next(served.glob("apache_ossie*.whl"))
    with zipfile.ZipFile(wheel, "a") as package:
        package.writestr(
            "tampered.txt", "Modified after the release checksums were generated"
        )
    # Update only the index link so uv downloads the changed wheel before
    # rejecting it against the original hash in the installation requirements.
    index = served / "simple" / "apache-ossie" / "index.html"
    text = index.read_text()
    original = text.split("#sha256=", 1)[1].split('"', 1)[0]
    index.write_text(
        text.replace(original, hashlib.sha256(wheel.read_bytes()).hexdigest()),
        encoding="utf-8",
    )
    with serve(served) as base:
        requirements_at(served, base)
        result = run(
            tmp_path,
            environment,
            "uv",
            "pip",
            "install",
            "--python",
            venv,
            "--require-hashes",
            "--only-binary",
            ":all:",
            "-r",
            f"{base}/requirements.txt",
        )
    assert result.returncode != 0
    assert "hash mismatch" in (result.stdout + result.stderr).lower()
