from __future__ import annotations

from enum import auto

from hex_sl_utils.utils import AutoName


class PlaceholderStyle(AutoName):
    JINJA = auto()
    QMARK = auto()
    FORMAT = auto()
    NUMERIC = auto()
    ASYNCPG = auto()
    COLON_NAMED = auto()
    DOLLAR_NAMED = auto()
    AT_NAMED = auto()
    PYFORMAT = auto()
    CLICKHOUSE = auto()
