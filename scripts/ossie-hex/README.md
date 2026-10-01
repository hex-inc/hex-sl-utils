# Preview of Vendor → Ossie → Hex conversion

This installer provides the Git-only `ossie-hex` converter together with seven
vendor converters through a single `ossie-preview` command. The converter and
`hex-sl-utils` come from the **same pinned commit** of this repository. Ossie's
Python models and the other converters come from a separate pinned commit of
[Hex's Apache Ossie fork][hex-inc/apache-ossie]. The full commit IDs are
recorded at the top of `install.sh` and printed during installation.

This repository does not publish `ossie-hex` to PyPI; Apache owns that release
process. Rerun the installer to pick up newly selected pins. Git source
revisions are fixed; third-party registry dependencies are resolved at
installation time.

By default, the preview environment and its raw executables live under
`~/.local/share/ossie-preview`. Only the `ossie-preview` dispatcher is added to
the normal user-level executable directory. Installation stops if that command
name is already owned by something else.

## Install

Ensure [`uv`](https://docs.astral.sh/uv/getting-started/installation/) is
installed.

On macOS and Linux, install the converter suite:

```sh
curl -LsSf \
  https://raw.githubusercontent.com/hex-inc/hex-sl-utils/main/scripts/ossie-hex/install.sh |
  sh
```

This installs Hex together with the `databricks`, `dbt`, `honeydew`, `nvidia`,
`omni`, `orionbelt`, and `wisdom` importers. Run the same command again to
update.

Use `ossie-preview <converter> --help` to inspect any converter. For example:

```sh
ossie-preview hex --help
ossie-preview databricks --help
```

## Conversion

Each workflow has two explicit stages. Keep the intermediate Ossie YAML when
investigating warnings or information lost between formats.

Import Vendor → Ossie

```sh
# Databricks Metric View → Ossie
ossie-preview databricks import \
  -i metric_view.yaml \
  -o model.ossie.yaml

# dbt
# first, generate the semantic manifest. then
ossie-preview dbt msi-to-ossie \
  -i target/semantic_manifest.json \
  -o model.ossie.yaml

# Honeydew
ossie-preview honeydew honeydew-to-ossie \
  -i honeydew-workspace/ \
  -o model.ossie.yaml

# Nvidia GSF
ossie-preview nvidia import \
  -i model.gsf.yaml \
  -o model.ossie.yaml

# Omni
ossie-preview omni import \
  -i omni-model/ \
  -o model.ossie.yaml

# Orionbelt
ossie-preview orionbelt obml-to-ossie \
  -i model.obml.yaml \
  -o model.ossie.yaml

# Snowflake does not provide an exporter yet.

# Wisdom
ossie-preview wisdom wisdom-to-ossie \
  -i domain-export.json \
  -o model.ossie.yaml
```

Export Ossie → Hex

```sh
ossie-preview hex export \
  -i model.ossie.yaml \
  -o hex-output/
```

See the [Ossie–Hex package README][ossie-hex-readme] for more details.

## Uninstall

Uninstall the complete converter suite:

```sh
curl -LsSf \
  https://raw.githubusercontent.com/hex-inc/hex-sl-utils/main/scripts/ossie-hex/install.sh |
  sh -s -- uninstall
```

## Current limitations

- GoodData has a Python conversion API but no command-line entry point.
- Snowflake currently converts from Ossie to Snowflake, not the reverse.
- Salesforce and Polaris use Java builds and are not installable as `uv` tools.

If the tool directory is not already on `PATH`, follow the installer's prompt
to run `uv tool update-shell` and restart the shell.

[hex-inc/apache-ossie]: https://github.com/hex-inc/apache-ossie
[ossie-hex-readme]: ../../packages/ossie-hex/README.md

## Updating installation pins

1. Commit and test the converter changes in Hex. Choose a full 40-character
   commit containing both `packages/ossie-hex` and `packages/hex-sl-utils`.
2. Update `HEX_REV` in `install.sh` in a subsequent commit. A commit cannot
   contain its own hash. Ensure the selected commit is pushed and retained on a
   durable branch or tag before distributing the installer. If a squash or
   rebase changes its identity, select the resulting commit and update the pin.
3. When updating Ossie, change the Git `rev` in the converter's
   `pyproject.toml`, regenerate the root `uv.lock`, and update `OSSIE_REV` to
   match. Recheck the vendor package paths and executable names at that
   revision.
4. Run `just test-scripts`, `just test-workspace`, `just test-ossie`, and the
   artifact smoke tests.

For local validation, `OSSIE_PREVIEW_HEX_REPO_URL` and
`OSSIE_PREVIEW_OSSIE_REPO_URL` can point to local `file:///...` Git
repositories. `OSSIE_PREVIEW_HEX_REV` and `OSSIE_PREVIEW_OSSIE_REV` select
candidate commits; branches and abbreviated hashes are rejected. Set
`XDG_DATA_HOME` and `UV_TOOL_BIN_DIR` to temporary directories to isolate the
environment and the public dispatcher from an existing installation. For
example, from this repo:

```sh
preview_test_dir="$(mktemp -d)"
XDG_DATA_HOME="$preview_test_dir/data" \
UV_TOOL_BIN_DIR="$preview_test_dir/commands" \
OSSIE_PREVIEW_HEX_REPO_URL="file://$PWD" \
sh scripts/ossie-hex/install.sh
XDG_DATA_HOME="$preview_test_dir/data" \
  "$preview_test_dir/commands/ossie-preview" hex --help
```

The installer verifies `--help` on every installed executable before exposing
the dispatcher. The existing command-ownership checks also apply in test runs;
use a PATH without a conflicting `ossie-preview` command.
