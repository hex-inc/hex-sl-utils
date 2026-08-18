from __future__ import annotations

from hex_sl_utils._vendor.sqlglot import exp

from .datatype import DataType


def datatype_to_sqlglot(dt: DataType) -> exp.DataType:
    """Convert DataType to sqlglot DataType."""
    mapping = {
        DataType.NULL: exp.DataType.Type.NULL,
        DataType.NUMBER: exp.DataType.Type.DOUBLE,
        DataType.STRING: exp.DataType.Type.VARCHAR,
        DataType.DATE: exp.DataType.Type.DATE,
        DataType.TIME: exp.DataType.Type.TIME,
        DataType.TIMESTAMP: exp.DataType.Type.TIMESTAMP,
        DataType.TIMESTAMPTZ: exp.DataType.Type.TIMESTAMPTZ,
        DataType.BOOLEAN: exp.DataType.Type.BOOLEAN,
        DataType.OTHER: exp.DataType.Type.UNKNOWN,
    }
    return exp.DataType.build(mapping[dt])
