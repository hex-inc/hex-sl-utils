from __future__ import annotations

from typing import Any

from hex_sl_utils._vendor.sqlglot import exp


def extract_static_sqlglot_constant(expr: exp.Expression) -> tuple[bool, Any]:
    if isinstance(expr, exp.Literal):
        return (True, expr.to_py())
    else:
        return (False, None)
