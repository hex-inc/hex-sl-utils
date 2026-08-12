# pyright: reportCallIssue=false, reportIncompatibleVariableOverride=false
from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, TypeVar

from pydantic import Field, Tag

import hex_sl_utils._vendor.sqlglot.expressions as exp
from hex_sl_utils.calc.ast.base import ExprBase
from hex_sl_utils.calc.compiled import ExpressionKind, TypedSelectExpression
from hex_sl_utils.calc.errors import SemanticItemNotFoundError, TypeCheckError
from hex_sl_utils.calc.protocols import CalcDialect

if TYPE_CHECKING:
    from hex_sl_utils.calc.protocols import CalcSchema
    from hex_sl_utils.calc.visitor import CalcVisitor

T = TypeVar("T")


MANGLE_PREFIX = "*"


def mangle(name: str) -> str:
    """
    Mangle the column name representing a dimension or measure to avoid conflicts
    raw columns
    """
    return f"{MANGLE_PREFIX}{name}"


def is_mangled(name: str) -> bool:
    return name.startswith(MANGLE_PREFIX)


def unmangle(name: str) -> str:
    if is_mangled(name):
        return name[len(MANGLE_PREFIX) :]
    else:
        return name


class Column(ExprBase):
    name: str = Field(description="Column name", alias="name")
    qualifiers: tuple[str, ...] = Field(
        default_factory=tuple, description="Dataset qualifiers"
    )

    @classmethod
    def tag(cls) -> Tag:
        return Tag("column")

    def accept(self, visitor: CalcVisitor[T]) -> T:
        return visitor.visit_column(self)

    def compile(
        self,
        schema: CalcSchema,
        dialect: CalcDialect,
        substitutions: dict[str, TypedSelectExpression],
        skip_mangle: bool | list[str] | None = None,
    ) -> TypedSelectExpression:
        """
        Compile the column to a sqlglot expression.

        Args:
            schema: The schema to compile the column against.
            substitutions: A dictionary of expressions to substitute for select
                           column names.

        Returns:
            TypedSelectExpression: The typed select expression

        Raises:
            SemanticItemNotFoundError: If an unqualified column is not found.
            TypeCheckError: If a qualified cross-dataset reference is not found.
        """

        # Check for qualified substitution first (e.g., "carriers.Name")
        if self.qualifiers:
            qualified_key = ".".join(self.qualifiers + (self.name,))
            if qualified_key in substitutions:
                return substitutions[qualified_key]

        # Check for unqualified substitution
        if self.name in substitutions:
            return substitutions[self.name]
        elif self.name in schema:
            if skip_mangle is True or (
                isinstance(skip_mangle, list) and self.name in skip_mangle
            ):
                sqlglot_column = exp.column(self.name, quoted=True)
            else:
                sqlglot_column = exp.column(mangle(self.name), quoted=True)

            return TypedSelectExpression(
                expression=sqlglot_column,
                data_type=schema[self.name],
                kind=ExpressionKind.COLUMN,
            )
        else:
            if self.qualifiers:
                # For qualified columns (cross-dataset references), if we reach here
                # it means the substitution wasn't provided.
                qualified_name = ".".join(self.qualifiers + (self.name,))
                msg = (
                    f"Cross-dataset reference '{qualified_name}' not found "
                    f"in substitutions"
                )
                raise TypeCheckError(msg)
            else:
                available = {*substitutions.keys(), *schema.keys()}
                msg = f"Column {self.name} not found in schema"
                raise SemanticItemNotFoundError(
                    msg,
                    item_name=self.name,
                    item_type="dimension",
                    case_insensitive_matches=SemanticItemNotFoundError.find_case_insensitive_matches(
                        self.name, available
                    ),
                )


TaggedColumnExpr = Annotated[Column, Column.tag()]
