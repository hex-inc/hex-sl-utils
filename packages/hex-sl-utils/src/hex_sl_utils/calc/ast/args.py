from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import RootModel

if TYPE_CHECKING:
    from hex_sl.calc.ast.expr import CalcExpr


class Args(RootModel[list["CalcExpr"]]):
    model_config = {
        "json_schema_extra": {
            "title": "Args",
            "description": "Function arguments.",
        }
    }

    def __hash__(self) -> int:
        return hash(tuple(self.root))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Args):
            return False
        # mypy doesn't believe that this returns a boolean
        return bool(self.model_dump() == other.model_dump())
