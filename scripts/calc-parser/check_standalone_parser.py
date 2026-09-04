#!/usr/bin/env python3
"""Check if the standalone parser is up to date with the grammar file."""

import hashlib
import re
import sys
from pathlib import Path

from lark import __version__ as lark_version

project_root = Path(__file__).parent.parent.parent
calc_source = project_root / "packages/hex-sl-utils/src/hex_sl_utils/calc"
grammar_path = calc_source / "grammar.lark"
parser_path = calc_source / "_calc_parser_standalone.py"

if not parser_path.exists():
    print(f"ERROR: Standalone parser not found at {parser_path}")
    print("\nTo generate the standalone parser, run:")
    print("  just build-calc-parser")
    sys.exit(1)

grammar_hash = hashlib.sha256(grammar_path.read_bytes()).hexdigest()
parser_content = parser_path.read_text()
hash_match = re.search(r"Grammar hash: ([a-f0-9]{64})", parser_content)
version_match = re.search(r"Lark version: ([^\n]+)", parser_content)

if hash_match is None or version_match is None:
    print(f"ERROR: Generation metadata is missing from {parser_path}")
    print("\nTo regenerate the standalone parser, run:")
    print("  just build-calc-parser")
    sys.exit(1)

if hash_match.group(1) != grammar_hash or version_match.group(1) != lark_version:
    print("ERROR: Standalone parser is out of date")
    print(f"  Grammar hash: {grammar_hash}")
    print(f"  Parser hash:  {hash_match.group(1)}")
    print(f"  Lark version: {lark_version}")
    print(f"  Parser Lark:  {version_match.group(1)}")
    print("\nTo regenerate the standalone parser, run:")
    print("  just build-calc-parser")
    sys.exit(1)

print("✓ Standalone parser is up to date with grammar file")
print(f"  Grammar hash: {grammar_hash}")
print(f"  Lark version: {lark_version}")
sys.exit(0)
