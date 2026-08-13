from __future__ import annotations

from typing import Literal

from hex_sl_common.exceptions import UserFacingError

# List of all valid dialect names that can be passed to from_name()
DialectName = Literal[
    "athena",
    "alloydb",
    "bigquery",
    "clickhouse",
    "databricks",
    "duckdb",
    "motherduck",
    "mssql",
    "tsql",
    "mysql",
    "prestodb",
    "postgres",
    "redshift",
    "snowflake",
    "trino",
    "spark",
    "starburst",
]

# Canonical dialect names (after alias resolution)
SUPPORTED_DIALECTS: frozenset[str] = frozenset(
    [
        "bigquery",
        "clickhouse",
        "duckdb",
        "mssql",
        "mysql",
        "postgres",
        "redshift",
        "snowflake",
        "spark",
        "trino",
    ]
)

# Mapping from dialect aliases to canonical names
DIALECT_ALIASES: dict[str, str] = {
    "athena": "trino",
    "starburst": "trino",
    "prestodb": "trino",
    "tsql": "mssql",
    "databricks": "spark",
    "alloydb": "postgres",
    "motherduck": "duckdb",
}


def normalize_dialect_name(name: str) -> str:
    """Normalize a dialect name to its canonical form.

    This function:
    1. Lowercases the name
    2. Strips the "hex-sl-" prefix if present
    3. Resolves aliases to canonical names
    4. Validates the name is supported

    Args:
        name: The dialect name (case-insensitive, may include aliases)

    Returns:
        The canonical dialect name

    Raises:
        ValueError: If the dialect name is not supported
    """
    name = name.lower()

    # Strip hex-sl- prefix if present
    if name.startswith("hex-sl-"):
        name = name[7:]

    # Apply alias mapping
    canonical_name = DIALECT_ALIASES.get(name, name)

    # Validate
    if canonical_name not in SUPPORTED_DIALECTS:
        msg = f"Unsupported dialect: {name}"
        raise UserFacingError(msg)

    return canonical_name
