# Contributing

## Repository structure

This repository is a [uv workspace][uv-workspaces]. Each directory under
`packages/` is an independently versioned, publishable Python distribution.
The repository shares one development environment and one cross-platform
lockfile.

```text
.
├── packages/
│   └── hex-sl-utils/
│       ├── pyproject.toml
│       ├── src/hex_sl_utils/
│       └── tests/
├── scripts/
├── pyproject.toml
└── uv.lock
```

The root project contains shared development configuration and is never
published. Runtime dependencies and package metadata belong to the package
that uses them.

## Setup

The packages require CPython 3.11 or newer. Python 3.14 is the default local
development version; CI currently tests Python 3.11 through 3.14 on Linux and
smoke tests Python 3.14 on macOS and Windows.

```bash
uv sync --all-packages
uv run --all-packages poe ci
```

Useful commands:

```bash
uv run --all-packages poe check       # lint, format-check, and type-check
uv run --all-packages poe format      # apply automatic formatting and fixes
uv run --all-packages poe test        # run all tests
uv run --all-packages poe test-cov    # run tests and write coverage.xml
uv run --all-packages poe build       # build every publishable package
uv run --all-packages poe smoke-test  # test each built artifact in isolation
uv lock --upgrade                     # intentionally update dependencies
```

Commit `uv.lock`. Normal CI commands use `--locked`; update the lockfile
explicitly with `uv lock --upgrade`.

## Adding a package

Create `packages/<distribution-name>/pyproject.toml` and use a `src` layout:

```text
packages/example-package/
├── pyproject.toml
├── README.md
├── src/example_package/
│   ├── __init__.py
│   └── py.typed
└── tests/
    └── smoke_test.py
```

The `packages/*` workspace glob and repository-level test/type-check commands
discover it automatically. If one workspace member depends on another, declare
the dependency normally in `[project.dependencies]` and add a workspace source
in that member:

```toml
[tool.uv.sources]
hex-sl-utils = { workspace = true }
```

Every distribution owns its runtime dependencies, README, version, and build
metadata. It must also provide an executable `tests/smoke_test.py` that imports
its public API and checks any package data needed at import time. Do not put
runtime dependencies in the root development group.

## Package boundaries

- `hex-sl-utils`: Hex resource models, resource parsing/loading, and the
  generated resource schema.
- Add a new distribution only when it has an independent consumer, dependency
  set, or release lifecycle. Folders alone are sufficient for internal modules.
- Prefer explicit imports between distributions. Do not split one Python import
  namespace across multiple wheels.

## Tests and database support

Unit tests live beside the package they exercise. Repository-wide integration
tests may live in top-level `tests/` once they exist. Mark tests requiring an
external service with `@pytest.mark.integration` and database-specific tests
with `@pytest.mark.database`.

Do not add every database driver to the default development environment.
Introduce a named dependency group for each integration suite when it is
needed, and run it in a dedicated CI job with the corresponding service. This
keeps the fast, cross-platform unit-test matrix independent of Docker and native
database clients.

## Generated schemas

Generated schemas should be package data beneath the package's `src` tree so
they are included in wheels by the build backend. Put the generator in
`scripts/`, expose it as a Poe task, and add a CI check that runs the generator
and fails when `git diff --exit-code` reports stale output. Test both schema
content and its presence in a built wheel.

## Before opening a pull request

```bash
uv run --all-packages poe check
uv run --all-packages poe test
uv run --all-packages poe build
uv run --all-packages poe smoke-test
```

The `build` task builds a wheel and source distribution for every workspace
package with uv source overrides disabled.

The `smoke-test` task installs each artifact by itself in a fresh isolated
environment and runs that package's smoke test, following
[uv's distribution-testing recommendation][uv-publish]. This catches missing
package data and undeclared dependencies used by eager imports. Lazy and
optional code paths still require focused unit and integration tests.

[uv-publish]: https://docs.astral.sh/uv/guides/integration/github/#publishing-to-pypi
[uv-workspaces]: https://docs.astral.sh/uv/concepts/projects/workspaces/
