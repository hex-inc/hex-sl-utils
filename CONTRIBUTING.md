# Contributing

## Local environment

[Devbox][devbox] is the source of truth for the system tools used across this
workspace. It provides the pinned versions without requiring contributors to
install each toolchain independently.

Install [direnv][direnv] and configure its hook for your shell. Then authorize
the repository environment and install the workspace dependencies:

```bash
direnv allow
devbox run setup
```

- Run `direnv allow` again after `.envrc` changes.
- Run `devbox run setup` again when dependency lockfiles change.

Run the complete local CI workflow after setup:

```bash
devbox run ci
```

## Common commands

Run workspace commands from the repository root. Devbox scripts are the public
interface for routine development tasks, regardless of which underlying
toolchain they invoke.

```bash
devbox run check       # lint, format-check, and type-check
devbox run format      # apply automatic formatting and fixes
devbox run test        # run all tests
devbox run test-cov    # run tests and write coverage reports
devbox run build       # build every publishable package, artifact
devbox run verify      # verify build outputs
devbox run smoke-test  # test built artifacts in isolation
devbox run ci          # run checks, tests, builds, and smoke tests
```

Add or update a Devbox script when a command is useful across the workspace.
Keep narrowly scoped package or tool commands in that component's own
documentation.

## Understanding the workspace

The repository root owns shared development concerns: the Devbox environment,
task entry points, CI configuration, workspace-level dependency configuration,
and policies that apply to every package. The root project is not published.

Publishable units live under `packages/`. Each package owns its runtime
dependencies, version, public documentation, source, tests, build metadata, and
release lifecycle. Consult the README or contributing guide beside a package
before changing its public behavior or package-specific workflow.

Repository-wide tooling lives under `scripts/`. Generators, release helpers,
artifact checks, and similar tools should document their specialized setup and
commands alongside their implementation. Tests that exercise several packages
or the workspace as a whole may live in a top-level `tests/` directory; tests
for one package should remain with that package.

Create a new package only when a component has an independent consumer,
dependency set, or release lifecycle. Internal organization alone does not
require another publishable unit. Keep dependencies between packages explicit
and avoid splitting one import namespace across multiple distributions.

## Shared workspace conventions

- Commit environment and dependency lockfiles. CI and routine commands use
  locked dependency resolution.
- Add system-level tools to `devbox.json`, not to undocumented workstation
  setup instructions.
- Keep runtime dependencies with the package that imports them. Root dependency
  configuration is for shared development tooling only.
- Add workspace-wide commands to `devbox.json`. Package-only commands belong
  with the package or tool that uses them.
- Keep the default development environment lightweight. Optional integrations
  and external services should use dedicated dependency groups and CI jobs.

## Python toolchain

Python packages form a [uv workspace][uv-workspaces]. Configure each package for
their minimum supported Python version in the `pyproject.toml` file. The
workspace otherwise targets the latest stable Python version.

Declare shared Python development dependencies in the root `pyproject.toml`.
Declare runtime dependencies in the consuming package's `pyproject.toml`. When
one workspace package depends on another, declare the dependency normally and
add a uv workspace source in the consuming package:

```toml
[tool.uv.sources]
hex-sl-utils = { workspace = true }
```

Use a `src` layout for publishable Python packages. Each distribution must
include a package README and an executable smoke test that imports its public
API and verifies package data required at runtime. Smoke tests are run against
the declared Python versions in the project configuration file (typically a
floor and ceiling version).

```toml pyproject.toml
[tool.smoke-test]
python-versions = ["3.9", "3.14"]
```

Update Python dependencies intentionally and commit `uv.lock`:

```bash
uv lock --upgrade
```

## JavaScript and TypeScript toolchain

Node.js and pnpm are available through Devbox for repository tooling such as
code generators. JavaScript packages belong to the root pnpm workspace when
one is present, while each package owns its dependencies and scripts in its
`package.json`.

The workspace `check` and `format` commands use Oxlint and Oxfmt for TypeScript
sources. Oxlint runs its stable type-aware rules and discovers the relevant
`tsconfig.json` for each TypeScript package. Keep TypeScript formatting and
lint configuration at the workspace root unless one package has a documented
need for an override.

Run pnpm commands from the repository root so they use the workspace and its
root lockfile. Target a specific tooling package with a pnpm filter rather than
creating package-local lockfiles. Commit `pnpm-lock.yaml` with intentional
dependency changes.

## Tests and external services

Unit tests should remain close to the package they exercise. Integration tests
that require databases, network services, or native clients should be marked
and run in dedicated CI jobs with explicit dependencies. Do not add every
integration driver or service to the default development environment.

For Python tests, use `@pytest.mark.integration` for tests crossing an external
boundary and `@pytest.mark.database` for database-specific coverage.

## Generated artifacts

Keep generators under `scripts/` and generated output with the package that
distributes or consumes it. Expose generation and staleness checks as Devbox
scripts, commit intentional generated changes with their source changes, and
enforce freshness in CI.

Test both the generated content and its presence in the built artifact. A
generator-specific contributing guide should explain any additional workflow
or troubleshooting steps.

## Before opening a pull request

Run the same aggregate workflow used for local validation:

```bash
devbox run ci
```

The build command creates every publishable artifact. The smoke-test command
installs each artifact by itself in a fresh environment and exercises its public
entry point (following [uv's distribution-testing recommendation][uv-publish]
for Python distributions). This catches missing package data and undeclared
eager dependencies; lazy and optional paths still require focused tests.

## Publishing

Packages are released independently using tags of the form
`<distribution>-v<version>`, for example `hex-sl-utils-v0.1.0`. The tag must
exactly match a workspace distribution name and the version in that package's
`pyproject.toml`.

### One-time repository setup

1. Create a protected GitHub environment named `pypi`. Require maintainer
   approval for deployments to that environment.
2. Create the package project on PyPI.
3. In the PyPI project's publishing settings, add this repository and
   `.github/workflows/publish.yml` as a Trusted Publisher using the `pypi`
   environment.
4. Repeat the Trusted Publisher configuration for each distribution added to
   the workspace.

No long-lived PyPI token is stored in GitHub. The workflow exchanges GitHub's
short-lived identity token for publishing credentials.

### Versioning policy

Every distribution has a static [PEP 440][pep-440] version in its own
`pyproject.toml`. Versions are independent: releasing one workspace package
does not require changing any other package's version.

The default branch should normally carry the next anticipated development
version using the `.dev0` suffix. For example, after releasing `0.1.0`, begin
the next development cycle with `0.2.0.dev0`. Changes accumulate under the
package changelog's `Unreleased` heading during this phase. Development
versions identify unreleased source and must not be published.

A release pull request removes `.dev0` and updates the changelog. Final,
prerelease (`aN`, `bN`, or `rcN`), and post-release versions may be published;
`.devN` versions may not. The non-development version exists on `main` long
enough to tag and publish the release. A follow-up pull request then advances
the package to its next `.dev0` version.

This policy is enforced by `scripts/release.py`: publishing requires a tag that
exactly matches the distribution name and metadata version, and the validator
rejects any version for which PEP 440 reports `is_devrelease`. Tests in
`tests/test_release.py` cover both the accepted and rejected forms.

### Releasing a package

1. Open a release pull request that:
   - sets a non-development version in the package's `pyproject.toml`;
   - moves the package's changes from `Unreleased` to that version in its
     `CHANGELOG.md`;
   - refreshes `uv.lock`; and
   - passes `devbox run ci`.

2. Merge the release pull request to `main`.
3. Create an annotated tag at that merge commit and push it:

   ```bash
   git tag -a hex-sl-utils-v0.1.0 -m "hex-sl-utils 0.1.0"
   git push origin hex-sl-utils-v0.1.0
   ```

4. Review and approve the `pypi` environment deployment. The publish workflow
   validates the tag and metadata, reruns checks and tests, then builds and
   smoke-tests the selected package. A separate job with publishing credentials
   downloads and publishes those exact artifacts through Trusted Publishing.
5. Open a follow-up pull request setting the next development version, such as
   `0.2.0.dev0`, and restore an empty `Unreleased` section.

Published files are immutable. If publishing fails after any artifact reaches
PyPI, fix the issue and release a new version; never move or reuse a release
tag.

[devbox]: https://www.jetify.com/docs/devbox/
[direnv]: https://direnv.net/docs/hook.html
[uv-publish]: https://docs.astral.sh/uv/guides/integration/github/#publishing-to-pypi
[uv-workspaces]: https://docs.astral.sh/uv/concepts/projects/workspaces/
[pep-440]: https://packaging.python.org/en/latest/specifications/version-specifiers/
