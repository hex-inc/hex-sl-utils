#!/usr/bin/env python3
"""Check if the standalone parser is up to date with the grammar file."""

import hashlib
import re
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
calc_path = project_root / "packages" / "hex-sl-utils" / "src" / "hex_sl_utils" / "calc"
grammar_path = calc_path / "grammar.lark"
parser_path = calc_path / "_calc_parser_standalone.py"

# Check if parser file exists
if not parser_path.exists():
    print(f"ERROR: Standalone parser not found at {parser_path}")
    print("\nTo generate the standalone parser, run:")
    print("  devbox run build:calc")
    sys.exit(1)

# Read and hash the current grammar
grammar_content = grammar_path.read_text()
current_grammar_hash = hashlib.sha256(grammar_content.encode()).hexdigest()

# Read the parser file and extract the grammar hash from header
parser_content = parser_path.read_text()
hash_match = re.search(r"Grammar hash: ([a-f0-9]{64})", parser_content)

if not hash_match:
    print(f"ERROR: No grammar hash found in {parser_path}")
    print("\nThe standalone parser file is missing the grammar hash in its header.")
    print("To regenerate the standalone parser, run:")
    print("  devbox run build:calc")
    sys.exit(1)

stored_grammar_hash = hash_match.group(1)

# Compare hashes
if current_grammar_hash != stored_grammar_hash:
    print("ERROR: Standalone parser is out of date")
    print(f"  Grammar hash: {current_grammar_hash}")
    print(f"  Parser hash:  {stored_grammar_hash}")
    print("\nThe grammar file has changed since the standalone parser was generated.")
    print("To regenerate the standalone parser, run:")
    print("  devbox run build:calc")
    sys.exit(1)

print("✓ Standalone parser is up to date with grammar file")
print(f"  Grammar hash: {current_grammar_hash}")
sys.exit(0)
