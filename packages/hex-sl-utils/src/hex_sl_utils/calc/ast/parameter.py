from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, TypeVar

from pydantic import Field, Tag

from hex_sl._vendor.sqlglot import exp
from hex_sl.calc.ast.base import ExprBase
from hex_sl.datatype import DataType, datatype_to_sqlglot
from hex_sl.expr import ExpressionKind, TypedSelectExpression
from hex_sl.utils import TypeCheckError

if TYPE_CHECKING:
    from hex_sl.calc.visitor import CalcVisitor

T = TypeVar("T")


class Parameter(ExprBase):
    parameter: str = Field(
        description="Parameter name", json_schema_extra={"title": "ParameterName"}
    )

    @classmethod
    def tag(cls) -> Tag:
        return Tag("parameter")

    def accept(self, visitor: CalcVisitor[T]) -> T:
        return visitor.visit_parameter(self)

    def compile(
        self,
        parameter_types: dict[str, DataType],
    ) -> TypedSelectExpression:
        """
        Compile the parameter to a sqlglot expression.

        Args:
            parameter_types: A dictionary of parameter names to data types.

        Returns:
            TypedSelectExpression: The typed select expression

        Raises:
            TypeCheckError: If the parameter name is not found in the
                            parameter types.
        """
        if self.parameter in parameter_types:
            parameter_type = parameter_types[self.parameter]
            return TypedSelectExpression(
                expression=exp.Placeholder(
                    this=self.parameter, kind=datatype_to_sqlglot(parameter_type)
                ),
                data_type=parameter_type,
                kind=ExpressionKind.SCALAR,
            )
        else:
            msg = f"Parameter {self.parameter} not found in parameter types"
            raise TypeCheckError(msg)


TaggedParameterExpr = Annotated[Parameter, Parameter.tag()]
