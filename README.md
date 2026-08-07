# Hex semantic layer

Libraries for working with the Hex semantic-layer format and integrations.

This project is in its **initial development phase**. The first milestone is to
publicly release the Hex semantic resource models, project loaders, and
generated schemas into a public, standalone library. The APIs and package names
may change until the first stable release.

## Packages

### `hex-sl-utils` (Python)

_Status: Not yet published._

Models and I/O for Hex semantic resources.

#### Design goals

- Consumers should be able to parse, validate, inspect, and generate Hex
  semantic resources.
- Support projects like [Apache Ossie](https://ossie.apache.org/).

## Installation

The packages are not published yet. Once available, install with:

```bash
uv add hex-sl-utils

# or
python -m pip install hex-sl-utils
```

Python 3.11 or newer is required.

For repository setup, development commands, package structure, and the release
process, see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

This project and its published packages are licensed under the
[Apache License 2.0](LICENSE).
