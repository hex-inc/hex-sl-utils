# Contributing to schema generation

## Local environment

The generator uses Python 3.14 and uv to produce JSON Schema, then Node.js 24
and pnpm 11 to produce TypeScript declarations. The repository's Devbox
configuration pins all four tools.

From the repository root:

```shell
devbox run setup
devbox shell
```

`setup` synchronizes the Python workspace and installs the locked pnpm
workspace dependencies. If you manage the tools yourself, run the equivalent
commands directly:

```shell
uv sync --all-packages
pnpm install --frozen-lockfile
```

Run pnpm commands from the repository root so pnpm uses
`pnpm-workspace.yaml` and the root `pnpm-lock.yaml`.

## Generate and verify artifacts

The public entry points are Poe tasks and should be run from the repository
root:

```shell
uv run --all-packages poe generate-schema
uv run --all-packages poe check-schema
```

`generate-schema` performs the following steps:

1. Generates JSON Schema from the Pydantic `Resource` model.
2. Installs the locked pnpm dependencies.
3. Runs the `build` script in this workspace package.
4. Validates the generated TypeScript declarations for self-references.

The artifacts are written beneath
`packages/hex-sl-utils/src/hex_sl_utils/schema_files`. Commit intentional
artifact changes together with their generator or model changes.

`check-schema` regenerates the artifacts and fails if the result differs from
the committed files. CI runs this guard on every pull request.

To invoke only the TypeScript stage while iterating on its transforms, first
generate or update the JSON Schema, then run:

```shell
pnpm --filter @hex/sl-utils-scripts-schema run build
```

## Dependency changes

Add or update JavaScript dependencies through the workspace from the
repository root. For example:

```shell
pnpm --filter @hex/sl-utils-scripts-schema add --save-dev <package>
```

Commit both `scripts/schema/package.json` and `pnpm-lock.yaml`. Do not create a
package-local lockfile or restore `package-lock.json`.

Python development dependencies belong in the root `pyproject.toml` and are
locked in `uv.lock`.

## Before opening a pull request

Run the schema guard and its focused tests:

```shell
uv run --all-packages poe check-schema
uv run pytest packages/hex-sl-utils/tests/test_schema.py
```

The complete repository check is available as:

```shell
devbox run ci
```
