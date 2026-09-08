import hex_sl_utils.dialect.registration  # noqa: F401
from hex_sl_utils.dialect.dialect import Dialect
from hex_sl_utils.dialect.dialect_name import (
    DIALECT_ALIASES,
    DIALECT_NAMES,
    SUPPORTED_DIALECTS,
    CanonicalDialectName,
    DialectName,
    normalize_dialect_name,
)

__all__ = [
    "DIALECT_ALIASES",
    "DIALECT_NAMES",
    "SUPPORTED_DIALECTS",
    "CanonicalDialectName",
    "Dialect",
    "DialectName",
    "normalize_dialect_name",
]
