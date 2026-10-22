"""
Operator type definitions for the calc language.

This module defines the supported binary and unary operators in the calc language
as Literal types for type safety and consistency across the codebase.
"""

from __future__ import annotations

from typing import Literal, Union

# Type definitions for calc language operators
OperandType = Literal["left", "right", "unary"]

BinaryOp = Literal[
    "+", "-", "*", "/", "^", "%", "||", "&&", "<", "<=", ">", ">=", "=", "!="
]

UnaryOp = Literal["-", "+", "!"]

CalcOp = Union[BinaryOp, UnaryOp]

__all__ = [
    "BinaryOp",
    "CalcOp",
    "OperandType",
    "UnaryOp",
]
