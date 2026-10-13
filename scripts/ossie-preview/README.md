# Python converter previews

Build Apache Ossie's unpublished Python converters into wheels hosted by
[GitHub Releases][github-releases]. Each preview contains the selected converter
and its matching Apache Ossie SDK. Runtime dependencies come from PyPI.

## Source pins

`sources.toml` declares the shared Apache commit, package identities, and source
directories. A converter can override the shared pin:

```toml
commit = "2b1f9bfccb558a98b21e4d4576e072fb14a5d952"

[converters.omni]
package = "ossie-omni"
directory = "converters/omni"
# commit = "<another full commit SHA>"
```

An override selects both the converter and its SDK from that commit. Builds
download the immutable snapshot and discard it after building. Local workspace
packages and their development pins do not enter previews.

Supported Python packages:

| Converter | Wheel package | Interface |
| --- | --- | --- |
| Hex | `ossie-hex` | `ossie-hex` |
| dbt | `apache-ossie-dbt` | `ossie-dbt` |
| Cube | `apache-ossie-cube` | `ossie-cube` |
| GoodData | `apache-ossie-gooddata` | Python API |
| Holistics | `apache-ossie-holistics` | `ossie-holistics` |
| Honeydew | `apache-ossie-honeydew` | `ossie-honeydew` |
| Microsoft | `apache-ossie-microsoft` | `ossie-microsoft` |
| NVIDIA | `apache-ossie-nvidia-auto-ontology` | `ossie-nvidia-auto-ontology` |
| Omni | `ossie-omni` | `ossie-omni` |
| Ontology | `apache-ossie-ontology` | Python API |
| OrionBelt | `apache-ossie-orionbelt` | `ossie-orionbelt` |
| Sigma | `apache-ossie-sigma` | `ossie-sigma` |
| Snowflake | `apache-ossie-snowflake` | `ossie-snowflake` |
| ThoughtSpot | `apache-ossie-thoughtspot` | `ossie-thoughtspot` |
| Wisdom | `apache-ossie-wisdom` | `ossie-wisdom` |
| Wisdom Semantic View | `apache-ossie-wisdom-semantic-view` | `ossie-wisdom-semantic-view` |

## Build and test locally

From the repository root, select one converter (Hex is the default):

```bash
# Build without tests, or build and test real installation and conversion.
just scripts-ossie-preview-build --converter omni
just scripts-ossie-preview-test omni
```

Each build resolves PyPI dependencies from the two built wheels and writes exact
versions and hashes into the release's `requirements.txt`. CI tests and
publishes that same payload. There are no checked-in converter dependency locks;
rebuilding the same Apache commit can select newer dependencies. Published
releases retain their original pins.

Assets go to `dist/ossie-preview-<converter>/`, or `dist/ossie-preview/` for
Hex.

Tests install the wheels into private managed Python 3.12 with real uv and
hash-enforced requirements, without Git or system Python on PATH. They verify
converted content, exercise reverse conversion where the packaged interface
supports it, and reject modified wheels. GoodData and Ontology use their Python
APIs; Holistics tests AML export without requiring the external Holistics CLI.
Wisdom Semantic View uses its upstream finance fixture to test the supported
subset of that format.

## Publish

Dispatch the [preview workflow][preview-workflow] on `main` with `converter`, a
unique `release_id` such as `v2026.10.13`, and `publish=true`. The workflow
tests that converter's exact artifacts on Linux, macOS, and Windows before
publishing. Other converters run only when explicitly selected; automatic PR and
`main` checks retain the existing Hex default.

Each release contains two wheels, `requirements.txt`, `RELEASE_NOTES.md`, and
`SHA256SUMS`. Release notes identify the publisher and Apache source commits.
Checksums verify the tested payload before publication. Tags use
`ossie-preview/<converter>/<release_id>`, with Hex retaining
`ossie-preview/<release_id>` for existing consumers.

## Consume

Consumers install without a source checkout or local compilation:

```bash
uv venv --managed-python --python 3.12 .venv
uv pip install --python .venv --require-hashes --only-binary :all: \
  -r "<requirements.txt download URL>"
```

Activate the environment, then use the converter's native command or Python API.
For example:

```bash
ossie-omni export -i model.ossie.yaml -o omni/
ossie-omni import -i omni/ -o restored.ossie.yaml
```

[github-releases]: https://github.com/hex-inc/hex-sl-utils/releases
[preview-workflow]: ../../.github/workflows/ossie-preview.yml
