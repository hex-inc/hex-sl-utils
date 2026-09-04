#!/usr/bin/env python3
"""
Vendor sqlglot library into hex_sl_utils._vendor.sqlglot

This script downloads sqlglot from GitHub, rewrites its internal imports
to use the vendored namespace, and places it in the hex_sl_utils package.

This version uses LibCST to preserve all formatting, comments, and style.
"""

import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import cast

try:
    import libcst as cst
except ImportError:
    print("LibCST is required for this script. Install with: pip install libcst")
    sys.exit(1)

import requests

# Configuration
SQLGLOT_VERSION = "v27.8.0"
SQLGLOT_REPO = "https://github.com/tobymao/sqlglot"
VENDOR_NAMESPACE = "hex_sl_utils._vendor"
PROJECT_ROOT = Path(__file__).parent.parent.parent
VENDOR_DIR = (
    PROJECT_ROOT
    / "packages"
    / "hex-sl-utils"
    / "src"
    / "hex_sl_utils"
    / "_vendor"
    / "sqlglot"
)


class SqlglotImportRewriter(cst.CSTTransformer):
    """CST transformer to rewrite sqlglot imports to use vendored namespace."""

    def __init__(self, vendor_namespace: str = VENDOR_NAMESPACE) -> None:
        self.vendor_namespace = vendor_namespace

    def leave_Import(
        self, original_node: cst.Import, updated_node: cst.Import
    ) -> cst.Import:
        """Handle 'import sqlglot' style imports."""
        new_names = []
        changed = False

        for name_item in updated_node.names:
            if isinstance(name_item, cst.ImportAlias):
                name = name_item.name

                # Check if this is a sqlglot import
                if isinstance(name, cst.Attribute):
                    # Handle import sqlglot.xxx
                    if self._get_full_name(name).startswith("sqlglot"):
                        # Convert to vendored import
                        new_name = self._rewrite_attribute(
                            name, "sqlglot", f"{self.vendor_namespace}.sqlglot"
                        )
                        new_names.append(name_item.with_changes(name=new_name))
                        changed = True
                        continue
                elif isinstance(name, cst.Name) and name.value == "sqlglot":
                    # Handle import sqlglot
                    if name_item.asname is None:
                        # import sqlglot -> import hex_sl_utils._vendor.sqlglot as sqlglot
                        new_name = cast(
                            cst.Attribute,
                            cst.parse_expression(f"{self.vendor_namespace}.sqlglot"),
                        )
                        new_names.append(
                            cst.ImportAlias(
                                name=new_name,
                                asname=cst.AsName(
                                    name=cst.Name("sqlglot"),
                                    whitespace_before_as=cst.SimpleWhitespace(" "),
                                    whitespace_after_as=cst.SimpleWhitespace(" "),
                                ),
                            )
                        )
                        changed = True
                        continue
                    else:
                        # import sqlglot as alias ->
                        #     import hex_sl_utils._vendor.sqlglot as alias
                        new_name = cast(
                            cst.Attribute,
                            cst.parse_expression(f"{self.vendor_namespace}.sqlglot"),
                        )
                        new_names.append(name_item.with_changes(name=new_name))
                        changed = True
                        continue

            new_names.append(name_item)

        if changed:
            return updated_node.with_changes(names=new_names)
        return updated_node

    def leave_ImportFrom(
        self, original_node: cst.ImportFrom, updated_node: cst.ImportFrom
    ) -> cst.ImportFrom:
        """Handle 'from sqlglot import ...' style imports."""
        if updated_node.module is None:
            return updated_node

        module_name = self._get_full_name(updated_node.module)

        if module_name == "sqlglot" or module_name.startswith("sqlglot."):
            # Rewrite to vendored import
            new_module_name = f"{self.vendor_namespace}.{module_name}"
            new_module = cst.parse_expression(new_module_name)
            return updated_node.with_changes(module=new_module)

        return updated_node

    def _get_full_name(self, node) -> str:
        """Extract the full dotted name from a Name or Attribute node."""
        if isinstance(node, cst.Name):
            return node.value
        elif isinstance(node, cst.Attribute):
            return f"{self._get_full_name(node.value)}.{node.attr.value}"
        else:
            return ""

    def _rewrite_attribute(self, node, old_prefix: str, new_prefix: str):
        """Recursively rewrite an Attribute node to use a new prefix."""
        if isinstance(node, cst.Name):
            if node.value == old_prefix:
                return cst.parse_expression(new_prefix)
            return node
        elif isinstance(node, cst.Attribute):
            new_value = self._rewrite_attribute(node.value, old_prefix, new_prefix)
            return node.with_changes(value=new_value)
        return node

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.Call:
        """Handle function calls that might contain sqlglot module paths in strings."""
        # Check if this is an import_module call
        func_name = None
        if isinstance(updated_node.func, cst.Name):
            func_name = updated_node.func.value
        elif isinstance(updated_node.func, cst.Attribute):
            # Handle importlib.import_module
            func_name = updated_node.func.attr.value

        if func_name == "import_module":
            # Process arguments
            new_args = []
            changed = False

            for arg in updated_node.args:
                if isinstance(arg.value, cst.FormattedString):
                    # Handle f-string arguments
                    new_parts = []
                    for part in arg.value.parts:
                        if isinstance(part, cst.FormattedStringText):
                            # Check if this part contains sqlglot
                            if "sqlglot." in part.value or part.value == "sqlglot":
                                new_value = part.value.replace(
                                    "sqlglot.", f"{self.vendor_namespace}.sqlglot."
                                )
                                new_value = new_value.replace(
                                    '"sqlglot"', f'"{self.vendor_namespace}.sqlglot"'
                                )
                                if new_value != part.value:
                                    new_parts.append(part.with_changes(value=new_value))
                                    changed = True
                                else:
                                    new_parts.append(part)
                            else:
                                new_parts.append(part)
                        else:
                            new_parts.append(part)

                    if changed:
                        new_args.append(
                            arg.with_changes(
                                value=arg.value.with_changes(parts=new_parts)
                            )
                        )
                    else:
                        new_args.append(arg)

                elif isinstance(arg.value, cst.SimpleString):
                    # Handle regular string arguments
                    string_value = arg.value.value
                    # Remove quotes to get the actual string content
                    quote_char = string_value[0]
                    inner_value = string_value[1:-1]

                    if "sqlglot." in inner_value or inner_value == "sqlglot":
                        new_inner = inner_value.replace(
                            "sqlglot.", f"{self.vendor_namespace}.sqlglot."
                        )
                        if inner_value == "sqlglot":
                            new_inner = f"{self.vendor_namespace}.sqlglot"
                        if new_inner != inner_value:
                            new_string_value = f"{quote_char}{new_inner}{quote_char}"
                            new_args.append(
                                arg.with_changes(
                                    value=cst.SimpleString(new_string_value)
                                )
                            )
                            changed = True
                        else:
                            new_args.append(arg)
                    else:
                        new_args.append(arg)
                else:
                    new_args.append(arg)

            if changed:
                return updated_node.with_changes(args=new_args)

        return updated_node


def rewrite_imports_in_file(
    file_path: Path, vendor_namespace: str = VENDOR_NAMESPACE
) -> bool:
    """
    Rewrite imports in a single Python file using LibCST.

    Returns True if the file was modified, False otherwise.
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            source = f.read()
    except UnicodeDecodeError:
        print(f"Warning: Skipping {file_path} due to encoding issues")
        return False

    # Quick check if file contains sqlglot imports
    if "sqlglot" not in source:
        return False

    try:
        # Parse the source code into CST
        tree = cst.parse_module(source)
    except cst.ParserSyntaxError as e:
        print(f"Warning: Error parsing {file_path}: {e}")
        return False

    # Transform the CST
    transformer = SqlglotImportRewriter(vendor_namespace)
    modified_tree = tree.visit(transformer)

    # Check if any modifications were made
    if modified_tree.deep_equals(tree):
        return False

    # Write back to file (preserves all formatting)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(modified_tree.code)

    return True


def download_sqlglot(version: str = SQLGLOT_VERSION) -> Path:
    """Download sqlglot from GitHub and return path to extracted directory."""
    print(f"Downloading sqlglot {version}...")

    url = f"{SQLGLOT_REPO}/archive/refs/tags/{version}.zip"
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    # Save to temporary file
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp_file:
        tmp_file.write(response.content)
        tmp_path = Path(tmp_file.name)

    # Extract to temporary directory
    extract_dir = Path(tempfile.mkdtemp())
    with zipfile.ZipFile(tmp_path, "r") as zip_ref:
        zip_ref.extractall(extract_dir)

    # Clean up zip file
    tmp_path.unlink()

    # Find the extracted directory (usually sqlglot-{version without v})
    version_num = version.lstrip("v")
    extracted = extract_dir / f"sqlglot-{version_num}"

    if not extracted.exists():
        # Try to find any sqlglot directory
        for item in extract_dir.iterdir():
            if item.is_dir() and "sqlglot" in item.name:
                extracted = item
                break

    if not extracted.exists():
        msg = f"Could not find extracted sqlglot directory in {extract_dir}"
        raise RuntimeError(msg)

    return extracted / "sqlglot"


def clean_vendor_directory(vendor_dir: Path) -> None:
    """Clean or create the vendor directory."""
    if vendor_dir.exists():
        print(f"Cleaning existing vendor directory: {vendor_dir}")
        shutil.rmtree(vendor_dir)

    vendor_dir.parent.mkdir(parents=True, exist_ok=True)


def copy_sqlglot_source(source_dir: Path, vendor_dir: Path) -> None:
    """Copy sqlglot source to vendor directory."""
    print(f"Copying sqlglot source to {vendor_dir}")
    shutil.copytree(source_dir, vendor_dir)


def cleanup_unnecessary_files(vendor_dir: Path) -> None:
    """Remove unnecessary files from vendored sqlglot."""
    print("Cleaning up unnecessary files...")

    patterns_to_remove = [
        "**/__pycache__",
        "**/*.pyc",
        "**/*.pyo",
        "**/tests",
        "**/test_*.py",
        "**/*_test.py",
        "**/testing",
        "**/benchmarks",
        "**/.git*",
        "**/docs",
        "**/examples",
        "**/*.md",
        "**/*.rst",
        "**/*.txt",
        "**/Makefile",
        "**/setup.py",
        "**/setup.cfg",
        "**/pyproject.toml",
        "**/tox.ini",
        "**/.coverage*",
        "**/.*rc",
        "**/.*yml",
        "**/.*yaml",
    ]

    for pattern in patterns_to_remove:
        for path in vendor_dir.rglob(pattern):
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                shutil.rmtree(path)


def rewrite_vendored_imports(vendor_dir: Path) -> None:
    """Rewrite all imports within the vendored sqlglot code."""
    print("Rewriting imports in vendored sqlglot...")

    modified_count = 0
    for py_file in vendor_dir.rglob("*.py"):
        if rewrite_imports_in_file(py_file):
            modified_count += 1
            print(f"  Modified: {py_file.relative_to(vendor_dir)}")

    print(f"Modified {modified_count} files")


def create_vendor_init_files() -> None:
    """Create __init__.py files for the vendor namespace."""
    vendor_root = VENDOR_DIR.parent

    # Create _vendor/__init__.py if it doesn't exist
    vendor_init = vendor_root / "__init__.py"
    if not vendor_init.exists():
        vendor_init.parent.mkdir(parents=True, exist_ok=True)
        vendor_init.write_text('"""Vendored dependencies for hex_sl_utils."""\n')
        print(f"Created {vendor_init}")


def create_version_file(vendor_dir: Path, version: str) -> None:
    """Create a _version.py file for the vendored sqlglot.

    sqlglot's _version.py is normally generated by setuptools-scm at build time,
    so it's not present in the source archive we download. Without it, sqlglot's
    __init__.py logs an error on import.
    """
    version_num = version.lstrip("v")
    version_tuple = tuple(int(x) for x in version_num.split("."))

    version_content = (
        f'__version__ = version = "{version_num}"\n'
        f"__version_tuple__ = version_tuple = {version_tuple}\n"
    )

    version_path = vendor_dir / "_version.py"
    version_path.write_text(version_content)
    print(f"Created {version_path}")


def add_vendor_readme(vendor_dir: Path, version: str) -> None:
    """Add a README to the vendored sqlglot directory."""
    readme_content = f"""# Vendored sqlglot

This directory contains a vendored copy of sqlglot version {version}.

Original repository: <{SQLGLOT_REPO}>

## How to update

Run the vendoring script:

```bash
just build-vendoring
```

This will download sqlglot and update all imports.

## License

sqlglot is distributed under the MIT license.
See LICENSE in this directory.
"""

    readme_path = vendor_dir / "README_VENDOR.md"
    readme_path.write_text(readme_content)
    print(f"Created {readme_path}")


def copy_license(source_dir: Path, vendor_dir: Path) -> None:
    """Copy the sqlglot LICENSE file."""
    # Look for license file in parent of source_dir (the extracted root)
    for license_name in [
        "LICENSE",
        "LICENSE.txt",
        "LICENSE.md",
        "LICENCE",
        "LICENCE.txt",
    ]:
        license_path = source_dir.parent / license_name
        if license_path.exists():
            shutil.copy2(license_path, vendor_dir / "LICENSE")
            print(f"Copied license file from {license_path}")
            return

    print("Warning: Could not find sqlglot LICENSE file")


PATCHES_DIR = PROJECT_ROOT / "scripts" / "vendoring" / "patches" / "sqlglot"


def apply_vendor_patches() -> None:
    """Apply local patch files from scripts/vendoring/patches/ to the vendored code."""
    if not PATCHES_DIR.exists():
        return

    patches = sorted(PATCHES_DIR.glob("*.patch"))
    if not patches:
        return

    print(f"\nApplying {len(patches)} vendor patch(es)...")
    for patch in patches:
        print(f"  Applying: {patch.name}")
        result = subprocess.run(
            ["git", "apply", str(patch)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            print(f"  ERROR applying {patch.name}:")
            print(f"    {result.stderr.strip()}")
            sys.exit(1)


def main() -> None:
    """Main entry point for vendoring script."""
    print(f"Vendoring sqlglot {SQLGLOT_VERSION} into {VENDOR_DIR}")
    print("Using LibCST to preserve all formatting and comments")

    # Download sqlglot before touching the committed vendor directory. This keeps
    # the existing artifact intact if the network request or archive extraction
    # fails.
    sqlglot_source = download_sqlglot(SQLGLOT_VERSION)

    # Clean or create vendor directory only after the download is ready.
    clean_vendor_directory(VENDOR_DIR)
    create_vendor_init_files()

    # Copy source code
    copy_sqlglot_source(sqlglot_source, VENDOR_DIR)

    # Copy license file
    copy_license(sqlglot_source, VENDOR_DIR)

    # Clean up unnecessary files
    cleanup_unnecessary_files(VENDOR_DIR)

    # Rewrite imports within vendored code
    rewrite_vendored_imports(VENDOR_DIR)

    # Create _version.py (normally generated by setuptools-scm at build time)
    create_version_file(VENDOR_DIR, SQLGLOT_VERSION)

    # Add README
    add_vendor_readme(VENDOR_DIR, SQLGLOT_VERSION)

    # Clean up temporary files
    shutil.rmtree(sqlglot_source.parent.parent)

    # Apply local patches on top of vendored code
    apply_vendor_patches()

    print("\nVendoring complete!")
    print(f"sqlglot has been vendored to: {VENDOR_DIR}")
    print("\nNext steps:")
    print("1. Run tests to ensure everything works correctly")
    print("2. Commit the vendored code to git")


if __name__ == "__main__":
    main()
