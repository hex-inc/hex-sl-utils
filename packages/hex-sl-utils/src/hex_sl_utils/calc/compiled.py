from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Union, cast, get_args

from hex_sl_utils._vendor.sqlglot import exp
from hex_sl_utils.types import DataType

from .errors import TypeCheckError


class ExpressionContext(str, Enum):
    """The SQL clause in which a compiled calc will be used."""

    PROJECTION = "projection"
    AGGREGATION = "aggregation"
    WHERE = "where"
    HAVING = "having"


class ExpressionKind(str, Enum):
    """The row/aggregation behavior of a compiled expression."""

    SCALAR = "scalar"
    COLUMN = "column"
    WINDOW = "window"
    AGGREGATION = "aggregation"

    @staticmethod
    def _validate_infer_kind(kinds: list[ExpressionKind]) -> ExpressionKind:
        kinds_set = set(kinds)
        if not kinds_set:
            return ExpressionKind.SCALAR
        if len(kinds_set) == 1:
            return next(iter(kinds_set))
        if kinds_set <= {ExpressionKind.SCALAR, ExpressionKind.COLUMN}:
            return ExpressionKind.COLUMN
        if kinds_set <= {
            ExpressionKind.SCALAR,
            ExpressionKind.COLUMN,
            ExpressionKind.WINDOW,
        }:
            return ExpressionKind.WINDOW
        if kinds_set <= {ExpressionKind.SCALAR, ExpressionKind.AGGREGATION}:
            return ExpressionKind.AGGREGATION
        msg = f"Cannot unify expression kinds: {kinds}"
        raise TypeCheckError(msg)


SelectExpression = Union[
    exp.Null,
    exp.Boolean,
    exp.Literal,
    exp.National,
    exp.Column,
    exp.Identifier,
    exp.Binary,
    exp.Unary,
    exp.Paren,
    exp.Func,
    exp.Case,
    exp.Cast,
    exp.Window,
    exp.Order,
    exp.Ordered,
    exp.Condition,
    exp.Predicate,
    exp.In,
    exp.Between,
    exp.WithinGroup,
    exp.AtTimeZone,
    exp.FromTimeZone,
    exp.Bracket,
    exp.Interval,
    exp.Comprehension,
    exp.Distinct,
    exp.Filter,
    exp.IgnoreNulls,
    exp.RespectNulls,
    exp.Introducer,
    exp.JSONPath,
    exp.JSONPathPart,
    exp.Lambda,
    exp.Tuple,
    exp.DataType,
    exp.DataTypeParam,
    exp.Star,
    exp.Var,
]
SelectExpressionTypes = get_args(SelectExpression)


def has_aggregate_function(expression: exp.Expression) -> bool:
    for node in expression.walk():
        if isinstance(node, exp.AggFunc):
            return True
        if isinstance(node, exp.Anonymous):
            name = str(node.this).lower()
            if "quantile" in name or "median" in name or "percentile" in name:
                return True
    return False


def has_window_function(expression: exp.Expression) -> bool:
    return any(isinstance(node, exp.Window) for node in expression.walk())


def has_column_references(expression: exp.Expression) -> bool:
    return any(
        isinstance(node, (exp.Column, exp.Identifier)) for node in expression.walk()
    )


def needs_parens_for_substitution(expression: exp.Expression) -> bool:
    return isinstance(expression, (exp.Binary, exp.Unary, exp.Concat))


@dataclass
class TypedSelectExpression:
    """A SQLGlot select expression with calc type and aggregation metadata."""

    expression: SelectExpression
    data_type: DataType
    kind: ExpressionKind

    @classmethod
    def from_sqlglot(
        cls,
        expression: exp.Expression,
        data_type: DataType,
        kind: ExpressionKind | None = None,
        strict: bool = False,
    ) -> TypedSelectExpression:
        """Create a validated typed SELECT expression."""
        if not isinstance(expression, SelectExpressionTypes):
            msg = (
                "Expected an expression compatible inside a SELECT, "
                f"found {type(expression).__name__}"
            )
            raise TypeCheckError(msg)

        if strict:
            invalid_nodes = [
                (node, type(node).__name__)
                for node in expression.walk()
                if not isinstance(node, SelectExpressionTypes)
            ]
            if invalid_nodes:
                sample_size = min(5, len(invalid_nodes))
                invalid_details = []
                for node, type_name in invalid_nodes[:sample_size]:
                    node_str = str(node)
                    if len(node_str) > 50:
                        node_str = node_str[:47] + "..."
                    invalid_details.append(f"{type_name}: {node_str}")

                invalid_list = "\n  - ".join(invalid_details)
                msg = (
                    f"Found {len(invalid_nodes)} invalid sub-expression(s) in "
                    f"the expression tree.\n"
                    f"Invalid expressions:\n  - {invalid_list}"
                )
                if len(invalid_nodes) > sample_size:
                    msg += f"\n  ... and {len(invalid_nodes) - sample_size} more"
                raise TypeCheckError(msg)

        if kind is None:
            kind = cls._infer_kind(expression)

        return cls(
            expression=cast(SelectExpression, expression),
            data_type=data_type,
            kind=kind,
        )

    @classmethod
    def _infer_kind(cls, expression: exp.Expression) -> ExpressionKind:
        if has_window_function(expression):
            return ExpressionKind.WINDOW
        if has_aggregate_function(expression):
            return ExpressionKind.AGGREGATION
        if has_column_references(expression):
            return ExpressionKind.COLUMN
        return ExpressionKind.SCALAR

    def inlinable(self) -> bool:
        return self.kind in (ExpressionKind.SCALAR, ExpressionKind.COLUMN)


def datatype_to_sqlglot(data_type: DataType) -> exp.DataType:
    mapping = {
        DataType.NULL: exp.DataType.Type.NULL,
        DataType.NUMBER: exp.DataType.Type.DOUBLE,
        DataType.STRING: exp.DataType.Type.VARCHAR,
        DataType.DATE: exp.DataType.Type.DATE,
        DataType.TIMESTAMP_NAIVE: exp.DataType.Type.TIMESTAMP,
        DataType.TIMESTAMP_TZ: exp.DataType.Type.TIMESTAMPTZ,
        DataType.BOOLEAN: exp.DataType.Type.BOOLEAN,
        DataType.OTHER: exp.DataType.Type.UNKNOWN,
    }
    return exp.DataType.build(mapping[data_type])
