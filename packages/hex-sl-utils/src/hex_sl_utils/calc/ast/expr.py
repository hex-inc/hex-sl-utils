from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any, Union, get_args

if TYPE_CHECKING:
    from hex_sl.dialect.base import HexSLDialect

if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias

from pydantic import Discriminator, Field, RootModel

from hex_sl.calc.ast.base import ExprBase, QualifiedColumnRef
from hex_sl.calc.ast.binary import TaggedBinaryExprUnion, binary_for_name
from hex_sl.calc.ast.column import Column, TaggedColumnExpr
from hex_sl.calc.ast.functions import TaggedFuncExprUnion, func_for_name
from hex_sl.calc.ast.literals import (
    LiteralBool,
    LiteralDate,
    LiteralNull,
    LiteralNumber,
    LiteralString,
    LiteralTimestamp,
    TaggedLiteralExprUnion,
)
from hex_sl.calc.ast.parameter import Parameter, TaggedParameterExpr
from hex_sl.calc.ast.sql_expression import SqlExpression, TaggedSqlExpression
from hex_sl.calc.ast.unary import TaggedUnaryExprUnion, unary_for_name
from hex_sl.calc.visitor import (
    AnyAggregateFunctionVisitor,
    CollectQualifiedColumnsVisitor,
)
from hex_sl.utils import UserFacingError

if TYPE_CHECKING:
    import polars as pl

    from hex_sl.calc.evaluation import DFCalcResult, ScalarCalcResult
    from hex_sl.dialect.base import HexSLDialect


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


def calc_expr_discriminator(v: Any) -> str:  # noqa: ANN401
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

    def eval(self) -> ScalarCalcResult:
        """
        Evaluate the scalar calc expression and return the result.

        Expression may not contain column references.

        Returns:
            ScalarCalcResult: The result of evaluating the calc expression.
        """
        from hex_sl.calc.evaluation import evaluate_scalar_calc

        return evaluate_scalar_calc(self)

    def eval_df(self, df: pl.DataFrame, date_as_object: bool = False) -> DFCalcResult:
        """
        Evaluate the calc expression against a pandas DataFrame.

        Column references in the expression are resolved against the provided DataFrame.

        Args:
            df (pl.DataFrame): The polars DataFrame to use as the schema and data
                               source.
            date_as_object (bool): Whether to return dates as objects.
                                   If False (the default), dates will be returned as
                                   datetime64[ns] dtype.

        Returns:
            DFCalcResult: The result of evaluating the calc expression.
        """
        from hex_sl.calc.evaluation import evaluate_df_calc

        return evaluate_df_calc(self, df, date_as_object)

    def substitute(
        self, substitutions: dict[str, ExprBase], dialect: HexSLDialect
    ) -> CalcExpr:
        """
        Substitute column references in the calc expression with the provided
        substitution expressions.

        Args:
            substitutions: Mapping of column names to replacement expressions
            dialect: SQL dialect
        """
        from hex_sl.calc.substitution import ColumnSubstitutionVisitor

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
        from hex_sl.calc.substitution import QualifyColumnsVisitor

        visitor = QualifyColumnsVisitor(dataset)
        result: ExprBase = self.root.accept(visitor)
        return result.to_expr()

    def get_unqualified_columns(self, dialect: HexSLDialect) -> list[str]:
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

    def get_all_columns(self, dialect: HexSLDialect) -> list[QualifiedColumnRef]:
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

    def has_aggregation(self, dialect: HexSLDialect) -> bool:
        visitor: AnyAggregateFunctionVisitor = AnyAggregateFunctionVisitor(dialect)
        result: bool = self.root.accept(visitor)
        return result

    def __hash__(self) -> int:
        return hash(self.root)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CalcExpr):
            return False
        return bool(self.root == other.root)
