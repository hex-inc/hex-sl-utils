# Preview of Vendor → Ossie → Hex conversion

This installer provides a preview of the unpublished `ossie-hex` converter along
with all other converters. The source is from
[Hex's fork of Apache Ossie][hex-inc/apache-ossie], specifically the
[`ossie-hex-preview` branch][ossie-hex-preview]. This branch will update with
the latest progress and fixes.

through a single `ossie-preview` command. They do not replace published uv
tools or claim the converters' eventual command names. Rerun the installer to
pick up fixes pushed to the preview branch.

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
ossie-preview dbt msi-to-osi \
  -i target/semantic_manifest.json \
  -o model.ossie.yaml

# Honeydew
ossie-preview honeydew honeydew-to-osi \
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
ossie-preview orionbelt obml-to-osi \
  -i model.obml.yaml \
  -o model.ossie.yaml

# Snowflake does not provide an exporter yet.

# Wisdom
ossie-preview wisdom wisdom-to-osi \
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
[ossie-hex-preview]: https://github.com/hex-inc/apache-ossie/tree/ossie-hex-preview
[ossie-hex-readme]: https://github.com/hex-inc/apache-ossie/blob/ossie-hex-preview/converters/hex/README.md
