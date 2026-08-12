# pyright: reportCallIssue=false, reportIncompatibleVariableOverride=false
from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any, Union, get_args

if TYPE_CHECKING:
    from hex_sl_utils.calc.compiled import ExpressionContext, TypedSelectExpression
    from hex_sl_utils.calc.protocols import CalcDialect, CalcSchema
    from hex_sl_utils.types import DataType

if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias

from pydantic import Discriminator, Field, RootModel

from hex_sl_utils.calc.ast.base import ExprBase, QualifiedColumnRef
from hex_sl_utils.calc.ast.binary import TaggedBinaryExprUnion, binary_for_name
from hex_sl_utils.calc.ast.column import Column, TaggedColumnExpr
from hex_sl_utils.calc.ast.functions import TaggedFuncExprUnion, func_for_name
from hex_sl_utils.calc.ast.literals import (
    LiteralBool,
    LiteralDate,
    LiteralNull,
    LiteralNumber,
    LiteralString,
    LiteralTimestamp,
    TaggedLiteralExprUnion,
)
from hex_sl_utils.calc.ast.parameter import Parameter, TaggedParameterExpr
from hex_sl_utils.calc.ast.sql_expression import SqlExpression, TaggedSqlExpression
from hex_sl_utils.calc.ast.unary import TaggedUnaryExprUnion, unary_for_name
from hex_sl_utils.calc.errors import UserFacingError
from hex_sl_utils.calc.visitor import (
    AnyAggregateFunctionVisitor,
    CollectQualifiedColumnsVisitor,
)

if TYPE_CHECKING:
    from hex_sl_utils.calc.protocols import CalcDialect


TaggedCalcExprUnion: TypeAlias = Union[
    TaggedBinaryExprUnion,
    TaggedUnaryExprUnion,
    TaggedFuncExprUnion,
    TaggedLiteralExprUnion,
    TaggedColumnExpr,
    TaggedParameterExpr,
    TaggedSqlExpression,
]


CalcExprUnionTypes = tuple(arg.__origin__ for arg in get_args(TaggedCalcExprUnion))
CalcExprUnionTypesSet = set(CalcExprUnionTypes)


def calc_expr_discriminator(v: Any) -> str:
    if isinstance(v, ExprBase):
        return v.tag().tag
    elif isinstance(v, dict):
        if "name" in v:
            return Column.tag().tag
        elif "parameter" in v:
            return Parameter.tag().tag
        elif "number" in v or "number_value" in v:
            return LiteralNumber.tag().tag
        elif "str" in v or "str_value" in v:
            return LiteralString.tag().tag
        elif "bool" in v or "bool_value" in v:
            return LiteralBool.tag().tag
        elif "timestamp" in v or "timestamp_value" in v:
            return LiteralTimestamp.tag().tag
        elif "date" in v or "date_value" in v:
            return LiteralDate.tag().tag
        elif "null" in v or "null_value" in v:
            return LiteralNull.tag().tag
        elif "sql" in v and "data_type" in v:
            return SqlExpression.tag().tag
        elif "unary" in v:
            unary_cls = unary_for_name(v["unary"])
            return unary_cls.tag().tag
        elif "binary" in v:
            binary_cls = binary_for_name(v["binary"])
            return binary_cls.tag().tag
        elif "fun" in v:
            func_cls = func_for_name(v["fun"])
            return func_cls.tag().tag

    msg = f"Unable to discriminate type for {v}"
    raise ValueError(msg)


class CalcExpr(RootModel[TaggedCalcExprUnion]):
    """
    A wrapper around `CalcExprUnion` class that serves to improve the
    representation of the AST when exporting to JSON Schema. By wrapping
    `CalcExprUnion`, we have better control over the schema generation,
    including adding metadata such as titles and descriptions.

    This class also provides a `to_string` method that delegates to the
    `to_string` method of the underlying expression, ensuring a consistent
    string representation of the entire AST.
    """

    root: TaggedCalcExprUnion = Field(
        ..., discriminator=Discriminator(calc_expr_discriminator)
    )

    model_config = {
        "json_schema_extra": {
            "title": "CalcExpr",
            "description": (
                "An expression that can be a binary operation, "
                "unary operation, function, or literal."
            ),
        }
    }

    def to_string(self) -> str:
        result: str = self.root.to_string()
        return result

    def compile(
        self,
        dialect: CalcDialect,
        *,
        context: ExpressionContext,
        schema: CalcSchema,
        timezone: str,
        parameters: dict[str, DataType] | None = None,
        substitutions: dict[str, TypedSelectExpression] | None = None,
        wrap_for_context: bool = True,
        skip_mangle: bool | list[str] | None = None,
    ) -> TypedSelectExpression:
        """Compile this calc using services supplied by a SQL dialect adapter."""
        from hex_sl_utils.calc.compiler import compile_calc_expression

        return compile_calc_expression(
            self,
            dialect=dialect,
            context=context,
            schema=schema,
            timezone=timezone,
            parameters=parameters,
            substitutions=substitutions,
            wrap_for_context=wrap_for_context,
            skip_mangle=skip_mangle,
        )

    def substitute(
        self, substitutions: dict[str, ExprBase], dialect: CalcDialect
    ) -> CalcExpr:
        """
        Substitute column references in the calc expression with the provided
        substitution expressions.

        Args:
            substitutions: Mapping of column names to replacement expressions
            dialect: SQL dialect
        """
        from hex_sl_utils.calc.substitution import ColumnSubstitutionVisitor

        visitor = ColumnSubstitutionVisitor(substitutions, dialect)
        result: ExprBase = self.root.accept(visitor)
        return result.to_expr()

    def qualify_unqualified_columns(self, dataset: str) -> CalcExpr:
        """
        Add dataset qualifiers to Column nodes that have no qualifiers.

        Args:
            dataset: Dataset name to set as the qualifier.

        Returns:
            A new CalcExpr with unqualified columns qualified to the dataset.
        """
        from hex_sl_utils.calc.substitution import QualifyColumnsVisitor

        visitor = QualifyColumnsVisitor(dataset)
        result: ExprBase = self.root.accept(visitor)
        return result.to_expr()

    def get_unqualified_columns(self, dialect: CalcDialect) -> list[str]:
        """Get unqualified column names only.

        Args:
            dialect: The SQL dialect

        Returns:
            List of column names from the local dataset context.

        Raises:
            ValueError: If expression contains cross-dataset (qualified) column
                references. Use get_all_columns() to handle cross-dataset references.
        """
        all_columns = self.get_all_columns(dialect)

        # Check for qualified columns
        qualified_refs = [(q, c) for q, c in all_columns if q]
        if qualified_refs:
            names = [".".join(q + (c,)) for q, c in qualified_refs]
            msg = (
                f"Expression contains cross-dataset references, "
                f"which are not supported in this context: {names}. "
            )
            raise UserFacingError(msg)

        # Return only unqualified column names
        return sorted(c for q, c in all_columns if not q)

    def get_all_columns(self, dialect: CalcDialect) -> list[QualifiedColumnRef]:
        """Get all column references with qualification info.

        Returns:
            List of (qualifiers, column_name) tuples where:
            - qualifiers is () for local/unqualified columns
            - qualifiers is ('dataset',) for cross-dataset references
        """
        visitor: CollectQualifiedColumnsVisitor = CollectQualifiedColumnsVisitor(
            dialect
        )
        result: list[QualifiedColumnRef] = sorted(self.root.accept(visitor))
        return result

    def has_aggregation(self, dialect: CalcDialect) -> bool:
        visitor: AnyAggregateFunctionVisitor = AnyAggregateFunctionVisitor(dialect)
        result: bool = self.root.accept(visitor)
        return result

    def __hash__(self) -> int:
        return hash(self.root)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CalcExpr):
            return False
        return bool(self.root == other.root)
