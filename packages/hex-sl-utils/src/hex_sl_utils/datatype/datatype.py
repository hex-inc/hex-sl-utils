from __future__ import annotations

from enum import auto

from hex_sl_common.utils import AutoName


class DataType(AutoName):
    NULL = auto()
    NUMBER = auto()
    STRING = auto()
    DATE = auto()
    TIME = auto()
    TIMESTAMP = auto()
    TIMESTAMPTZ = auto()
    BOOLEAN = auto()
    OTHER = auto()
