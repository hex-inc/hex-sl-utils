from typing import get_args

from hex_sl_utils.calc.ast.args import Args
from hex_sl_utils.calc.ast.expr import TaggedCalcExprUnion
from hex_sl_utils.calc.parser import parse_calc_expression

from .ast import CalcExpr
from .visitor import HEXSL_CALC_FN_NAME

# This is needed to resolve pydantic errors like:
#   pydantic.errors.PydanticUserError: `Args` is not fully defined; you should
#   define `CalcExpr`, then call `Args.model_rebuild()`
Args.model_rebuild()

# Rebuild all union types that make up CalcExpr
for union_type in get_args(TaggedCalcExprUnion):
    for cls in get_args(union_type):
        if hasattr(cls, "model_rebuild"):
            cls.model_rebuild()

__all__ = [
    "HEXSL_CALC_FN_NAME",
    "CalcExpr",
    "parse_calc_expression",
]
