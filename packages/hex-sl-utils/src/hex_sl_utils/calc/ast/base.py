from __future__ import annotations

import sys
from typing import TYPE_CHECKING, cast

if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias

from pydantic import BaseModel, ConfigDict, Tag

from hex_sl.utils import TypeCheckError

if TYPE_CHECKING:
    from hex_sl.calc.ast.expr import CalcExpr
    from hex_sl.calc.visitor import CalcVisitor, T

# Type alias for qualified column references
# Format: (qualifiers, column_name) where qualifiers is a tuple of dataset path
# components. Examples: ((), "col") for unqualified, (("dataset",), "col") for
# dataset.col
QualifiedColumnRef: TypeAlias = tuple[tuple[str, ...], str]


class ExprBase(BaseModel):
    """
    Base class for all expression types in the AST (Abstract Syntax Tree).

    This class serves as the foundation for all specific expression types,
    such as binary operations, unary operations, functions, and literals.
    It enforces that subclasses must implement the `to_string` method,
    which is used to convert the expression to its string representation.

    The `ExprBase` class is part of a hierarchy that allows for the creation
    of a flexible and extensible AST for the Calc Language.

    Relationship to other classes:
    - `CalcExprUnion`: A union of all possible concrete expression types
      (the leaves of the AST hierarchy), allowing for a single type that can
      represent any expression.
    - `CalcExpr`: A pydantic RootNode wrapper around `CalcExprUnion` that
      includes a description of the AST, and results in better a jsonschema
      structure.
    """

    # Allow both field names and aliases as input so that model_dump() output
    # (which uses field names by default) can be round-tripped back through
    # model_validate() without requiring by_alias=True on serialization.
    model_config = ConfigDict(populate_by_name=True)

    @classmethod
    def tag(cls) -> Tag:
        """
        Retrive the tag for use with pydantic discriminated unions.
        """
        msg = "Each subclass must implement its own tag."
        raise NotImplementedError(msg)

    def to_string(self) -> str:
        from hex_sl.calc.visitor import CalcToStringVisitor

        visitor = CalcToStringVisitor()
        return self.accept(visitor)

    def accept(self, visitor: CalcVisitor[T]) -> T:
        msg = "Each subclass must implement its own accept method."
        raise NotImplementedError(msg)

    def __hash__(self) -> int:
        return hash((type(self),) + tuple(self.__dict__.values()))

    def __eq__(self, other: object) -> bool:
        return hash(self) == hash(other)

    def to_expr(self) -> CalcExpr:
        from hex_sl.calc.ast.expr import (
            CalcExpr,
            CalcExprUnionTypesSet,
            TaggedCalcExprUnion,
        )

        # Check with type(self) in because isinstance is too with so many types
        if type(self) in CalcExprUnionTypesSet:
            self = cast(TaggedCalcExprUnion, self)
            return CalcExpr(root=self)
        else:
            msg = f"Expression is not a valid Calc Expression: {self}"
            raise TypeCheckError(msg)
