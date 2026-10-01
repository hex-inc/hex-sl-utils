# Ossie preview releases

Hex preview releases provide two pure Python wheels: `ossie-hex` from this
repository and `apache-ossie` from a pinned commit of upstream `apache/ossie`.
Published runtime dependencies, including `hex-sl-utils`, come from public PyPI
at pinned versions. Apache owns the official PyPI release process; Hex does
not publish either Ossie package to public PyPI.

Previews use Hex's existing S3/CloudFront Python package index at
[hex-internal-pypi-index.hex.tech](https://hex-internal-pypi-index.hex.tech/).
Existing `hex-sl` package listings and wheels are served without download
credentials in our checks. Confirm external customer network access before
launching CLI installation.

The initial scope is Ossie → Hex. Vendor → Ossie converters can be added later.
The earlier Git-based, seven-vendor `ossie-preview` installer has been retired.
Existing installations are independent; use the
[previous installer's uninstall instructions][legacy-installer] to remove them.

## Install a selected preview

Hex CLI's automatic runtime provisioning is separate work. For now, developers
can install a preview with [uv](https://docs.astral.sh/uv/). Git and a
pre-existing Python installation are not required. Installation requires network
access; conversion runs locally afterward.

Choose a published preview identifier and replace `RELEASE-ID` below. Run these
commands in a new, empty directory so the private environment does not replace
a project's environment:

```bash
uv venv --managed-python --python 3.12 .venv
uv pip install --python .venv --require-hashes --only-binary :all: \
  -r 'https://hex-internal-pypi-index.hex.tech/ossie-preview/RELEASE-ID/requirements.txt'
uv run --no-project --python .venv python -I -m ossie_hex.cli export \
  -i model.ossie.yaml -o hex/
```

`requirements.txt` identifies the preview's simple package index, pins both
Ossie packages, and includes hashes for every wheel and pinned PyPI dependency.
Keep uv's default `first-index` strategy: the release index supplies only the
two Ossie packages, and all other packages resolve from public PyPI. Do not add
the index root or enable cross-index version selection for this installation.
`--only-binary :all:` prevents consumer-side compilation. Remove the private
`.venv` directory to uninstall this manual installation.

## Preview identity and index layout

Each preview is published under `ossie-preview/<release_id>/`:

```text
ossie-preview/<release_id>/
  apache_ossie-<upstream-version>-py3-none-any.whl
  ossie_hex-<converter-version>-py3-none-any.whl
  requirements.txt
  SOURCES.txt
  RELEASE_NOTES.md
  SHA256SUMS
  simple/
    index.html
    apache-ossie/index.html
    ossie-hex/index.html
```

The package pages link to the wheels with SHA256 hash fragments. The
installation URL selects the release-scoped index, so the same Apache
development version can appear in successive previews without replacing an
earlier wheel. We preserve upstream package versions and do not edit Apache's
source code. Select a specific preview URL; package versions alone do not
identify the preview.

This is a standard static Python package index hosted alongside `hex-sl`. It has
its own prefix and does not modify the existing root or package listings.

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

Both wheels include license notices. `SOURCES.txt` records repositories,
commits, and package subdirectories; `SHA256SUMS` covers wheels, requirements,
notes, and all simple-index pages.

The integration tests use real uv and an HTTP package index, with no Git or
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

## Configure publishing once

The existing `hex-sl` publisher uses CircleCI's `hex-pypi-global` context. Those
settings are not automatically available to this repository's GitHub Actions.
An infrastructure maintainer must configure the following before publishing:

1. Create a GitHub environment named `ossie-preview`, restricted to deployments
   from `main`.
2. Configure an AWS role for GitHub OIDC, trusting audience `sts.amazonaws.com`
   and subject `repo:hex-inc/hex-sl-utils:environment:ossie-preview`. Use a role
   with `s3:GetObject` and `s3:PutObject` on only the index bucket's
   `ossie-preview/*` prefix, KMS `GenerateDataKey` and `Decrypt` permissions for
   its existing encryption key, and `cloudfront:CreateInvalidation` for its
   existing distribution. No delete permission is needed. Confirm the existing
   CloudFront origin can serve the new prefix and decrypt these objects.
3. Add environment variables using the existing index's actual infrastructure
   values:

   | GitHub environment variable | Value |
   | --- | --- |
   | `PYPI_INDEX_AWS_IAM_ROLE_ARN` | Role with the GitHub OIDC trust above |
   | `PYPI_INDEX_AWS_S3_BUCKET_NAME` | Existing package index bucket |
   | `PYPI_INDEX_AWS_KMS_KEY_ARN` | Existing package index encryption key |
   | `PYPI_INDEX_AWS_CLOUDFRONT_DISTRIBUTION_ID` | Distribution serving the index domain |

The workflow uses region `us-east-2`, matching the existing index. AWS access
uses short-lived OIDC credentials; consumer installation does not require AWS
credentials. Ordinary pull-request builds and installation tests need none of
these publishing settings.

## Publish a preview

The **Ossie preview artifacts** workflow builds and tests candidates on pull
requests and relevant pushes to `main`. Installation is tested on Linux x64 and
ARM64, macOS Intel and ARM64, and Windows x64, using private Python 3.12.

After merging and configuring publishing, manually run that workflow on `main`
with a new `release_id`, such as `2026.10.01.1`, and `publish` checked. Leave
`publish` unchecked to only build and test.

Only after every installation job passes does CI verify the exact tested
payload and upload it to the release's prefix. It uses S3 conditional writes
(`If-None-Match: *`) to prevent overwrites. The checksum manifest reserves the
preview identity first; the installation requirements are uploaded last. A retry
can resume uploading the same bytes, but a changed payload requires a new ID.
CloudFront is then invalidated for only that preview's prefix. There are no
GitHub Release assets or public PyPI uploads in this workflow.

The publisher prints its upload plan without AWS requests by default. For
example, with your actual bucket and key:

```bash
uv run --locked python scripts/ossie-hex/publish.py candidate \
  --bucket INDEX-BUCKET --kms-key INDEX-KMS-KEY-ARN
```

Actual publishing requires AWS CLI v2 with conditional `put-object` support,
`--execute`, and `--distribution-id`. Use CI for publication so the
cross-platform checks gate it. After the first release, verify the installation
URL from outside Hex's network and run the documented installation before
integrating it into the CLI.

Once Apache publishes compatible packages, installation can use those releases
without changing the CLI's private-runtime approach.

[legacy-installer]: https://github.com/hex-inc/hex-sl-utils/blob/d010422/scripts/ossie-hex/README.md#uninstall
