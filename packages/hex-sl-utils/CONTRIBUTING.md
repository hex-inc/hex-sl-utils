# Contributing to hex-sl-utils

Start with the workspace [contributing guide](../../CONTRIBUTING.md) for local
setup, shared commands, and repository conventions.

Most contributors should use the workspace-wide Devbox commands. When working
only on `hex-sl-utils`, run these scoped equivalents from the repository root:

```bash
uv run --locked ruff check packages/hex-sl-utils
uv run --locked ruff format packages/hex-sl-utils
uv run --locked pyright packages/hex-sl-utils
uv run --locked --package hex-sl-utils pytest packages/hex-sl-utils/tests
uv build --package hex-sl-utils --no-sources
```

Package behavior and public API documentation live in [README.md](README.md).
