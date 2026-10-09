"""Verify a built preview, install it with real uv, and assert a local conversion."""

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

import pytest
import yaml
from constants import (
    DEFAULT_ASSETS_DIRECTORY,
    PYTHON_VERSION,
    RELEASE_REPOSITORY,
    SCRIPTS_DIRECTORY,
)

pytestmark = pytest.mark.integration


def test_release_payload(assets: Path) -> None:
    for wheel in assets.glob("*.whl"):
        with zipfile.ZipFile(wheel) as package:
            for notice in ("LICENSE", "NOTICE"):
                assert any(
                    name.endswith(f"/licenses/{notice}") for name in package.namelist()
                )
    sources = (assets / "RELEASE_NOTES.md").read_text()
    assert "https://github.com/apache/ossie/commit/" in sources
    assert "hex-inc/apache-ossie" not in sources
    requirements = (assets / "requirements.txt").read_text()
    assert "hex-sl-utils==" in requirements
    assert "git+" not in requirements
    assert "file:" not in requirements


def test_install_and_convert(assets: Path, tmp_path: Path) -> None:
    environment = _consumer_environment(tmp_path)
    venv = tmp_path / "venv"
    _assert_success(
        _run(
            tmp_path,
            environment,
            "uv",
            "venv",
            "--managed-python",
            "--python",
            PYTHON_VERSION,
            venv,
        )
    )
    served = tmp_path / "release"
    shutil.copytree(assets, served)
    with _serve(served) as base:
        _requirements_at(served, base)
        _assert_success(
            _run(
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
                "--index-url",
                "https://pypi.org/simple",
                "-r",
                f"{base}/requirements.txt",
            )
        )
    python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    _assert_success(
        _run(
            tmp_path,
            environment,
            python,
            "-I",
            "-c",
            "import importlib.metadata as m, pathlib, sys; "
            f"assert '.'.join(map(str, sys.version_info[:2])) == {PYTHON_VERSION!r}; "
            "assert m.distribution('hex-sl-utils').read_text('direct_url.json') is None; "
            f"assert pathlib.Path(sys.base_prefix).is_relative_to(pathlib.Path({str(tmp_path / 'python')!r}))",
        )
    )
    document = tmp_path / "model.ossie.yaml"
    shutil.copy2(Path(__file__).with_name("model.ossie.yaml"), document)
    output = tmp_path / "hex"
    command = venv / ("Scripts/ossie-hex.exe" if os.name == "nt" else "bin/ossie-hex")
    _assert_success(
        _run(
            tmp_path,
            environment,
            command,
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


def test_modified_wheel_is_rejected(assets: Path, tmp_path: Path) -> None:
    payload = tmp_path / "release"
    shutil.copytree(assets, payload)
    wheel = next(payload.glob("apache_ossie*.whl"))
    with zipfile.ZipFile(wheel, "a") as package:
        package.writestr("tampered.txt", "Modified after the checksums were generated")
    result = _verify_assets(payload)
    assert result.returncode != 0
    assert "Checksum mismatch" in result.stderr


def test_unexpected_asset_is_rejected(assets: Path, tmp_path: Path) -> None:
    payload = tmp_path / "release"
    shutil.copytree(assets, payload)
    (payload / "unexpected.whl").write_bytes(b"An asset outside the tested payload")
    result = _verify_assets(payload)
    assert result.returncode != 0
    assert "exactly the two wheels and release metadata" in result.stderr


@pytest.fixture(scope="module")
def assets() -> Path:
    """Consume artifacts built by the local recipe or downloaded by CI."""
    directory = Path(
        os.environ.get("OSSIE_PREVIEW_ASSETS", str(DEFAULT_ASSETS_DIRECTORY))
    ).resolve()
    _assert_success(_verify_assets(directory))
    return directory


def _verify_assets(directory: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPTS_DIRECTORY / "main.py"),
            "verify",
            "--assets",
            str(directory),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )


def _consumer_environment(directory: Path) -> dict[str, str]:
    """Expose real uv with private storage and no Git or Python on PATH."""
    executable = shutil.which("uv")
    assert executable is not None, "uv must be installed to run the integration test"
    tools = directory / "tools"
    tools.mkdir()
    shutil.copy2(executable, tools / Path(executable).name)
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("UV_", "PIP_", "PYTHON"))
        and key not in ("VIRTUAL_ENV", "CONDA_PREFIX")
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


def _run(
    directory: Path, environment: dict[str, str], *args: str | Path
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(arg) for arg in args],
        cwd=directory,
        env=environment,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )


def _assert_success(result: subprocess.CompletedProcess[str]) -> None:
    assert result.returncode == 0, result.stdout + result.stderr


@contextmanager
def _serve(directory: Path) -> Iterator[str]:
    """Serve actual release files over HTTP."""
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


def _requirements_at(directory: Path, base: str) -> None:
    """Keep wheel names and hashes while pointing downloads at the HTTP server."""
    path = directory / "requirements.txt"
    text = path.read_text()
    release_base = text.splitlines()[0].rsplit("/", 1)[0]
    assert release_base.startswith(
        f"https://github.com/{RELEASE_REPOSITORY}/releases/download/"
    )
    path.write_text(text.replace(release_base, base), encoding="utf-8")
