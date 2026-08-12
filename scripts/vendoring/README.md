# Vendoring Dependencies

## Overview

Vendoring a library avoids runtime dependencies on external packages. This makes
logic self-contained and easier to distribute in restricted environments. The
unique namespace allows it to coexist with another version of the dependency in
an embedding environment.

## Vendored Libraries

### sqlglot

- **Version**: 27.8.0
- **Location**: `packages/hex-sl-utils/src/hex_sl_utils/_vendor/sqlglot/`
- **Original repository**: <https://github.com/tobymao/sqlglot>
- **License**: MIT

## How Vendoring Works

1. The vendoring script downloads the library from GitHub
2. It uses LibCST (Concrete Syntax Tree) to rewrite imports while preserving all
   formatting
3. Unnecessary files (tests, docs, etc.) are removed
4. The production patches in `scripts/vendor_patches/` are applied
5. The library is placed in `hex_sl_utils._vendor.<library_name>`

## Updating Vendored Libraries

To update a vendored library:

1. Update the version in `scripts/vendoring/vendor_<library_name>.py`:

   ```python
   <LIBRARY_NAME>_VERSION = "vX.Y.Z"  # Change this to the new version
   ```

2. Run the vendoring script:

   ```bash
   devbox run build:vendoring
   ```

3. Copy the upstream license to `VENDORED_LICENSES` at the root of the
   repository and the root of packages that contain the vendoring. This may
   already be done.

4. Run tests to ensure everything works:

   ```bash
   devbox run test
   ```

5. Commit the changes

## Import Convention

All imports should use the vendored version:

```python
# Instead of:
from <library_name> import <symbol>

# Use:
from hex_sl_utils._vendor.<library_name> import <symbol>
```

## Technical Details

### LibCST-Based Import Rewriting

The vendoring script uses LibCST (Concrete Syntax Tree) instead of Python's
standard AST to preserve:

- All formatting (whitespace, line breaks, indentation)
- Comments (both inline and standalone)
- Quote styles (single vs double quotes)

### Import Patterns Handled

The rewriter handles these import patterns

- `import sqlglot` → `import hex_sl_utils._vendor.sqlglot as sqlglot`
- `import sqlglot.expressions` → `import hex_sl_utils._vendor.sqlglot.expressions` <!-- rumdl-disable-line line-length -->
- `from sqlglot import exp` → `from hex_sl_utils._vendor.sqlglot import exp`
- `from sqlglot.dialects import BigQuery` →
  `from hex_sl_utils._vendor.sqlglot.dialects import BigQuery`

### Files Removed During Vendoring

The following are removed to reduce size:

- Test files (`**/tests`, `**/test_*.py`, `**/*_test.py`)
- Documentation (`**/docs`, `**/*.md`, `**/*.rst`)
- Build configuration (`setup.py`, `pyproject.toml`, `Makefile`)
- Cache directories (`**/__pycache__`, `**/*.pyc`)
- Example files (`**/examples`)
