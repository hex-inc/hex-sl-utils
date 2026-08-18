import hex_sl_utils.dialect.registration  # noqa: F401
from hex_sl_utils.dialect.dialect import Dialect
from hex_sl_utils.dialect.dialect_name import (
    DIALECT_ALIASES,
    SUPPORTED_DIALECTS,
    DialectName,
    normalize_dialect_name,
)
from hex_sl_utils.dialect.placeholder import (
    PlaceholderConfig,
    PlaceholderStyle,
    set_placeholder_style,
)

__all__ = [
    "DIALECT_ALIASES",
    "SUPPORTED_DIALECTS",
    "Dialect",
    "DialectName",
    "PlaceholderConfig",
    "PlaceholderStyle",
    "normalize_dialect_name",
    "set_placeholder_style",
]
