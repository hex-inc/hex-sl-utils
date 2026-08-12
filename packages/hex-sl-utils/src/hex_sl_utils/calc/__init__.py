from typing import get_args

from hex_sl.calc.ast.args import Args
from hex_sl.calc.ast.expr import TaggedCalcExprUnion

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

__all__ = ["CalcExpr", "HEXSL_CALC_FN_NAME"]
