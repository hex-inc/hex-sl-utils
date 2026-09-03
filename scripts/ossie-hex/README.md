# Preview of Ossie <-> Hex converter

The `install-ossie-hex` script installs the unpublished `ossie-hex` command-line
converter from the public [`ossie-hex-preview` branch][ossie-hex-preview] of
[Hex's fork of Apache Ossie][hex-inc/apache-ossie]. It requires
[`uv`](https://docs.astral.sh/uv/getting-started/installation/).

## Installation

On macOS and Linux, install the converter with:

```sh
curl -fsSL \
  https://raw.githubusercontent.com/hex-inc/hex-sl-utils/main/scripts/ossie-hex/install.sh |
  sh
```

Update the converter by running the same command again.

## Usage

Convert an Ossie semantic model into a Hex semantic project:

```sh
ossie-hex export -i model.yaml -o hex-output/
```

Pass `--dialect` to select a SQL dialect:

See the source [package's README][ossie-hex-readme] for more details.

## Uninstallation

To uninstall the converter:

```sh
curl -fsSL \
  https://raw.githubusercontent.com/hex-inc/hex-sl-utils/main/scripts/ossie-hex/install.sh |
  sh -s -- uninstall
```

## Additional information

To install a specific branch, tag, or commit instead of the preview branch, set
`OSSIE_HEX_REF`:

```sh
curl -fsSL \
  https://raw.githubusercontent.com/hex-inc/hex-sl-utils/main/scripts/ossie-hex/install.sh |
  OSSIE_HEX_REF=<git-ref> sh
```

The installer uses `uv tool install` to create an isolated Python environment.
If the tool directory is not already on `PATH`, follow the installer's prompt to
run `uv tool update-shell` and restart the shell.

[hex-inc/apache-ossie]: https://github.com/hex-inc/apache-ossie
[ossie-hex-preview]: https://github.com/hex-inc/apache-ossie/tree/ossie-hex-preview
[ossie-hex-readme]: https://github.com/hex-inc/apache-ossie/blob/ossie-hex-preview/converters/hex/README.md
