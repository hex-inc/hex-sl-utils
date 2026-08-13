from typing import Annotated, Union

from hex_sl_utils.calc.ast.binary.comparison import (
    BinaryEqual,
    BinaryGreater,
    BinaryGreaterEqual,
    BinaryLess,
    BinaryLessEqual,
    BinaryNotEqual,
)
from hex_sl_utils.calc.ast.binary.logical import BinaryAnd, BinaryOr
from hex_sl_utils.calc.ast.binary.math import (
    BinaryDivide,
    BinaryMinus,
    BinaryModulus,
    BinaryMultiply,
    BinaryPlus,
    BinaryPower,
)
from hex_sl_utils.exception import UserFacingError

TaggedBinaryExprUnion = Union[
    Annotated[BinaryPlus, BinaryPlus.tag()],
    Annotated[BinaryMinus, BinaryMinus.tag()],
    Annotated[BinaryMultiply, BinaryMultiply.tag()],
    Annotated[BinaryDivide, BinaryDivide.tag()],
    Annotated[BinaryPower, BinaryPower.tag()],
    Annotated[BinaryModulus, BinaryModulus.tag()],
    Annotated[BinaryOr, BinaryOr.tag()],
    Annotated[BinaryAnd, BinaryAnd.tag()],
    Annotated[BinaryLess, BinaryLess.tag()],
    Annotated[BinaryLessEqual, BinaryLessEqual.tag()],
    Annotated[BinaryGreater, BinaryGreater.tag()],
    Annotated[BinaryGreaterEqual, BinaryGreaterEqual.tag()],
    Annotated[BinaryEqual, BinaryEqual.tag()],
    Annotated[BinaryNotEqual, BinaryNotEqual.tag()],
]


def binary_for_name(name: str) -> type[TaggedBinaryExprUnion]:
    name_lower = name.lower()
    if name_lower == "+":
        return BinaryPlus
    elif name_lower == "-":
        return BinaryMinus
    elif name_lower == "*":
        return BinaryMultiply
    elif name_lower == "/":
        return BinaryDivide
    elif name_lower in ("^", "**"):
        return BinaryPower
    elif name_lower == "%":
        return BinaryModulus
    elif name_lower in ("||", "or"):
        return BinaryOr
    elif name_lower in ("&&", "and"):
        return BinaryAnd
    elif name_lower == "<":
        return BinaryLess
    elif name_lower == "<=":
        return BinaryLessEqual
    elif name_lower == ">":
        return BinaryGreater
    elif name_lower == ">=":
        return BinaryGreaterEqual
    elif name_lower in ("=", "=="):
        return BinaryEqual
    elif name_lower in ("!=", "<>"):
        return BinaryNotEqual
    else:
        msg = f"Unknown binary operator: {name}"
        raise UserFacingError(msg)
