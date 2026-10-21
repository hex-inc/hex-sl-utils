# Preview of Apache Ossie converters

The Apache Ossie project, including vendor converters, is currently
awaiting publication to a public registry. Apache controls this process, and
presumably will release to PyPI. Until then, the necessary work can be made
available here, through
[GitHub Releases][github-releases].

The goal is to make Vendor → Ossie → Hex conversion installable by consumers
while those packages remain unpublished.

## What gets published

Each preview contains select vendor converters and their shared Apache Ossie
dependency from the pinned `hex-inc/apache-ossie-converters` Git submodule and
its nested `ossie` submodule. They are built into wheels so consumers can
install them without checking out source or compiling packages. Other runtime
dependencies come from PyPI.

The following artifacts are attached to a GitHub prerelease:

- Apache Ossie wheel: `apache_ossie-<version>-py3-none-any.whl`
- Vendor converter wheels: `<vendor-converter>-<version>-py3-none-any.whl`
- `requirements.txt`: the wheel URLs and shared pinned dependencies needed to
  install all converters in one environment.
- `RELEASE_NOTES.md`: the upstream and build configuration commits and combined
  dependency lock.
- `SHA256SUMS`: checksums for verifying the downloaded files.

## Publish and verify

The [Ossie preview artifacts workflow][preview-workflow] builds and tests
previews on pull requests and relevant changes to `main`. It installs the built
artifacts with real uv and private Python, then checks Vendor → Ossie → Hex
conversion, both Vendor conversion directions, and dbt → Ossie → Hex in that
same environment on Linux, macOS, and Windows. Checksums verify that the files
being published match the tested artifacts. Publication proceeds only after
every platform passes.

To make a preview available to consumers, a maintainer merges the changes and
runs that workflow on `main` with:

- `release_id`: a unique date version, such as `v2026.10.06` or `v2026.10.06-2`.
- `publish`: enabled.

CI builds, verifies, and uploads the artifacts to GitHub Releases. Maintainers
do not need to build or upload files manually.

A consumer selects a published preview using its identifier and the
`requirements.txt` download URL, and verifies the file using its SHA-256 digest
from `SHA256SUMS`.

## Install and convert

With uv installed, create an environment with managed Python 3.12 and install
from the selected preview's `requirements.txt` download URL:

```bash
uv venv --managed-python --python 3.12 .venv
uv pip install --python .venv --require-hashes --only-binary :all: \
  -r "<requirements.txt download URL>"
```

Activate the environment with `source .venv/bin/activate` on macOS or Linux,
or `.venv\Scripts\Activate.ps1` in Windows PowerShell. Each converter makes its
own command avaialable. Convert a Vendor specification to Ossie, then
to a Hex semantic project:

```bash
# vendor-converter import -i <input> -o model.ossie.yaml
ossie-hex export -i model.ossie.yaml -o hex/
```

## Develop and update locally

Run these commands from the repository root after `just setup-scripts`. Run
script tests with `just test-scripts-ossie-preview`. To build and test the
complete preview locally:

```bash
just test-scripts-ossie-preview-installation
```

The recipe builds into `dist/ossie-preview/` and tests those artifacts. To build
without running tests, using the current date as the preview label:

```bash
just build-scripts-ossie-preview
```

`bundle/pyproject.toml` selects which packages to release from the submodule.
`bundle/uv.lock` pins compatible dependencies so the converters install
together. Builds fail if this lock needs updating.

To update the converters, select a submodule revision, refresh the lock, and
test the result:

```bash
git -C external/apache-ossie-converters fetch origin <commit>
git -C external/apache-ossie-converters checkout --detach <commit>
git -C external/apache-ossie-converters submodule update --init --recursive
just lock-scripts-ossie-preview
just test-scripts-ossie-preview-installation
git add external/apache-ossie-converters scripts/ossie-preview/bundle/uv.lock
```

To refresh dependency versions, use `just lock-scripts-ossie-preview --upgrade`,
then test and commit the updated lock.

To add a Python converter, add its distribution name and source path to
`bundle/pyproject.toml`, refresh the lock, and add a conversion test.

Every wheel includes the LICENSE and NOTICE files from its own repository.

## Scripts

- `main.py`: builds and verifies preview releases.
- `constants.py`: shared paths, package sources, and runtime version.
- `build_wheels.py`: builds wheels from the pinned submodule.
- `release_artifacts.py`: writes release metadata and verifies the artifacts.
- `test_installation.py`: verifies artifacts and tests installation and
  conversion.

[github-releases]: https://github.com/hex-inc/hex-sl-utils/releases
[preview-workflow]: ../../.github/workflows/ossie-preview.yml
