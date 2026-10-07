# Preview of Apache Ossie and Hex conversion

The Apache Ossie project, and specifically Hex's converter, are currently
awaiting publication to a public registry. Apache controls this process, and
presumably will release to PyPI. Until then, the necessary work can be made
available here, through
[GitHub Releases][github-releases].

The goal is to make Ossie → Hex conversion installable by consumers while those
packages remain unpublished.

## What gets published

Each preview contains the Hex converter from this repository and Apache Ossie
from a pinned upstream commit. They are built into wheels so consumers can
install them without checking out source or compiling packages. Other runtime
dependencies come from PyPI.

The following artifacts are attached to a GitHub prerelease:

- Two wheels: `ossie-hex` and `apache-ossie`.
- `requirements.txt`: the wheel URLs and pinned dependencies needed to install.
- `RELEASE_NOTES.md`: the source commits used for the preview.
- `SHA256SUMS`: checksums for verifying the downloaded files.

## Publish and verify

The [Ossie preview artifacts workflow][preview-workflow] builds and tests
previews on pull requests and relevant changes to `main`. It installs the built
artifacts with real uv and private Python, then checks that conversion works on
Linux, macOS, and Windows. Checksums verify that the files being published match
the tested artifacts. Publication proceeds only after every platform passes.

To make a preview available to consumers, a maintainer merges the changes and
runs that workflow on `main` with:

- `release_id`: a unique date version, such as `v2026.10.06` or `v2026.10.06-2`.
- `publish`: enabled.

CI builds, verifies, and uploads the artifacts to GitHub Releases. Maintainers
do not need to build or upload files manually.

A consumer selects a published preview using its identifier and the
`requirements.txt` download URL, and verifies the file using its SHA-256 digest
from `SHA256SUMS`.

## Develop and update locally

Run these commands from the repository root. Make converter changes in
`packages/ossie-hex`, then build and test the resulting preview:

```bash
just scripts-ossie-preview-test
```

The recipe builds into `dist/ossie-preview/` and tests those artifacts. To build
without running tests, using the current date as the preview label:

```bash
just scripts-ossie-preview-build
```

To advance Apache Ossie, update its source commit in the converter's
`pyproject.toml`. Runtime dependency requirements are declared there too.
Refresh the dependency locks to select exact versions for the preview:

```bash
uv lock
just scripts-ossie-preview-lock
```

Review and commit the updated locks, then run `just scripts-ossie-preview-test`
again. CI repeats the installation and conversion checks before a preview is
published.

## Scripts

This process consists of the following scripts:

- `main.py`: command-line entrypoint for building, locking, and verifying.
- `constants.py`: shared paths, package sources, and runtime version.
- `build_wheels.py`: builds both packages and reads the upstream source pin.
- `release_artifacts.py`: writes release metadata and verifies the artifacts.
- `test_installation.py`: verifies artifacts and tests installation and
  conversion.

[github-releases]: https://github.com/hex-inc/hex-sl-utils/releases
[preview-workflow]: ../../.github/workflows/ossie-preview.yml
