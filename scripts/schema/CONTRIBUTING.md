# Contributing to schema generation

## Local environment

The generation script uses uv and Python to produce a JSON Schema and Node.js
and pnpm to produce TypeScript declarations. The repository's Devbox
configuration pins all four tools.

From the repository root:

```shell
devbox run setup
devbox shell
```

`setup` synchronizes the Python workspace and installs the locked pnpm
workspace dependencies.

## Generate and check artifacts

Run the workspace Devbox scripts from the repository root:

```shell
devbox run build:schema
devbox run verify:schema
```

`build:schema` builds the Python distributions, then runs
[`generate_schema.py`](generate_schema.py), which performs the following
steps:

1. Generates JSON Schema from the Pydantic `Resource` model.
2. Installs the locked pnpm dependencies.
3. Runs the `build` script in this workspace package.
4. Validates the generated TypeScript declarations for self-references.

The artifacts are written beneath
`packages/hex-sl-utils/src/hex_sl_utils/schema_files`. Commit intentional
artifact changes together with their generator or model changes.

`verify:schema` runs
[`check_generated_schema.py`](./check_generated_schema.py), regenerates the
artifacts, and fails if the result differs from the committed files. CI runs
this guard on every pull request.

Run the workspace checks after changing the generator or its TypeScript
transforms:

```shell
devbox run verify:schema
devbox run format
```

To invoke only the TypeScript stage while iterating on its transforms, first
generate or update the JSON Schema, then run:

```shell
devbox run -- pnpm --filter @hex/sl-utils-scripts-schema run build
```

Use this focused command only when the JSON Schema input is already current;
the workspace `build` script remains the normal entry point for generating the
complete artifact set.

## Dependency changes

Add or update JavaScript dependencies through the workspace from the
repository root. For example:

```shell
devbox run -- pnpm --filter @hex/sl-utils-scripts-schema add --save-dev <package>
```

Commit both `scripts/schema/package.json` and `pnpm-lock.yaml`. Do not create a
package-local lockfile or restore `package-lock.json`.

Python development dependencies belong in the root `pyproject.toml` and are
locked in `uv.lock`. Make intentional Python dependency changes through the
Devbox environment as well.

## Before opening a pull request

Verify the schema artifact matches regeneration.

```shell
devbox run verify:schema
```
