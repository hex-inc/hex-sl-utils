# Ossie preview releases

Hex preview releases provide two Python wheels: `ossie-hex` from this repository
and `apache-ossie` from a pinned commit of upstream `apache/ossie`. Published
runtime dependencies, including `hex-sl-utils`, come from PyPI at pinned
versions. Apache owns the official PyPI release process; these previews are
distributed only through
[GitHub Releases](https://github.com/hex-inc/hex-sl-utils/releases).

The initial scope is Ossie → Hex. Vendor → Ossie converters can be added later.
The earlier Git-based, seven-vendor `ossie-preview` installer has been retired.
Existing installations are independent; use the
[previous installer's uninstall instructions][legacy-installer] to remove them.

## Install a selected preview

Hex CLI's automatic runtime provisioning is separate work. For now, developers
can install a preview with [uv](https://docs.astral.sh/uv/). Git and a
pre-existing Python installation are not required. Installation requires network
access; conversion runs locally afterward.

Choose a release from GitHub and replace `RELEASE-ID` below with its identifier.
Run these commands in a new, empty directory so the private environment does not
replace a project's environment:

```bash
uv venv --managed-python --python 3.12 .venv
uv pip install --python .venv --require-hashes --only-binary :all: \
  -r 'https://github.com/hex-inc/hex-sl-utils/releases/download/ossie-preview%2FRELEASE-ID/requirements.txt'
uv run --no-project --python .venv python -I -m ossie_hex.cli export \
  -i model.ossie.yaml -o hex/
```

`requirements.txt` explicitly identifies both hosted wheels: GitHub Releases is
not a package index. Its hashes cover those wheels and every pinned PyPI runtime
dependency. `--only-binary :all:` prevents consumer-side compilation. Remove the
private `.venv` directory to uninstall this manual installation.

Preview identifiers are independent of Python distribution versions. Select a
specific release and its checksums, not a `latest` URL or the wheel's version
alone: two previews may use the same upstream development version.

## Build and test locally

Commit converter changes first so the release notes identify the exact source
used to build the wheel. Then, from the repository root:

```bash
just build-ossie-preview candidate
just test-ossie-preview
just build-packages
just smoke-test-packages
```

The build recipe writes `dist/ossie-preview/` and replaces a previous local
preview payload there. An optional second argument selects another output
directory. The underlying builder requires a fresh output directory unless
`--replace` is passed, and refuses to replace directories with unrelated files.

The payload contains:

- The `ossie-hex` and upstream `apache-ossie` wheels, with license notices.
- `requirements.txt`: release wheel URLs and pinned, hashed PyPI dependencies.
- `SOURCES.txt`: the repositories, commits, and package subdirectories.
- `RELEASE_NOTES.md`: preview identity and source provenance.
- `SHA256SUMS`: hashes of all the assets above.

The integration tests use real uv and an HTTP release server, with no Git or
Python on the consumer PATH. They provision private Python 3.12, install the
wheels and PyPI dependencies, assert a real conversion, and reject a modified
wheel. CI sets `OSSIE_PREVIEW_ASSETS` to test the exact payload it will publish.

## Update dependency pins

The converter's `pyproject.toml` pins upstream `apache/ossie` for development
and preview builds. Update that commit and regenerate `uv.lock` when advancing
Ossie.

`requirements.in` selects the published `hex-sl-utils` version. To refresh the
preview's runtime dependencies from the actual wheel metadata and PyPI, run:

```bash
just lock-ossie-preview
```

Review and commit `requirements.lock` with the corresponding source changes.
This lock is deliberately independent of workspace resolution; preview installs
must not use the local development copy of `hex-sl-utils`.

## Publish a preview

The **Ossie preview artifacts** workflow builds and tests candidates on pull
requests and relevant pushes to `main`. Installation is tested on Linux x64 and
ARM64, macOS Intel and ARM64, and Windows x64, using private Python 3.12.

After merging, manually run that workflow on `main` with:

- `release_id`: a new identifier, such as `2026.10.01.1`.
- `publish`: checked to publish, unchecked to only build and test.

Publishing occurs only after every installation job passes. The workflow
attaches the exact tested payload to the prerelease tag
`ossie-preview/<release_id>`. Existing releases are not overwritten, previews
are not marked as the repository's latest release, and their tags are excluded
from the PyPI workflow. No PyPI credentials are used.

Once Apache publishes compatible packages, installation can use those releases
without changing the CLI's private-runtime approach.

[legacy-installer]: https://github.com/hex-inc/hex-sl-utils/blob/d010422/scripts/ossie-hex/README.md#uninstall
