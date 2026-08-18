from enum import auto

from hex_sl_utils.utils import AutoName


class ExpressionContext(AutoName):
    PROJECTION = auto()
    AGGREGATION = auto()
    WHERE = auto()
    HAVING = auto()
