# Vendoring Dependencies

## Overview

hex_sl vendors the sqlglot library to avoid runtime dependencies on external packages, and to have full control over sql generation. This makes hex_sl self-contained and easier to distribute in restricted environments.

## Vendored Libraries

### sqlglot

- **Version**: 27.8.0
- **Location**: `src/hex_sl/_vendor/sqlglot/`
- **Original repository**: https://github.com/tobymao/sqlglot
- **License**: MIT

## How Vendoring Works

1. The vendoring script downloads sqlglot from GitHub
2. It uses LibCST (Concrete Syntax Tree) to rewrite imports while preserving all formatting
3. Unnecessary files (tests, docs, etc.) are removed
4. The library is placed in `hex_sl._vendor.sqlglot`

## Updating Vendored Libraries

To update the vendored sqlglot library:

1. Update the version in `scripts/vendor_sqlglot.py`:
   ```python
   SQLGLOT_VERSION = "v27.8.0"  # Change this to the new version
   ```

2. Run the vendoring script:
   ```bash
   pixi run vendor-sqlglot
   ```

3. Run tests to ensure everything works:
   ```bash
   pixi run test
   ```

4. Commit the changes

## Import Convention

All sqlglot imports in hex_sl use the vendored version:

```python
# Instead of:
from sqlglot import exp

# Use:
from hex_sl._vendor.sqlglot import exp
```

## Technical Details

### LibCST-Based Import Rewriting

The vendoring script uses LibCST (Concrete Syntax Tree) instead of Python's standard AST to preserve:
- All formatting (whitespace, line breaks, indentation)
- Comments (both inline and standalone)
- Quote styles (single vs double quotes)

### Import Patterns Handled

The rewriter handles these import patterns:

- `import sqlglot` → `import hex_sl._vendor.sqlglot as sqlglot`
- `import sqlglot.expressions` → `import hex_sl._vendor.sqlglot.expressions`
- `from sqlglot import exp` → `from hex_sl._vendor.sqlglot import exp`
- `from sqlglot.dialects import BigQuery` → `from hex_sl._vendor.sqlglot.dialects import BigQuery`

### Files Removed During Vendoring

The following are removed to reduce size:
- Test files (`**/tests`, `**/test_*.py`, `**/*_test.py`)
- Documentation (`**/docs`, `**/*.md`, `**/*.rst`)
- Build configuration (`setup.py`, `pyproject.toml`, `Makefile`)
- Cache directories (`**/__pycache__`, `**/*.pyc`)
- Example files (`**/examples`)
