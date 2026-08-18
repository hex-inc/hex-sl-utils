from __future__ import annotations

from dataclasses import dataclass
from typing import Union, cast, get_args

from hex_sl_utils._vendor.sqlglot import exp
from hex_sl_utils.datatype import DataType
from hex_sl_utils.exception import TypeCheckError

from .expr_inspection import (
    has_aggregate_function,
    has_column_references,
    has_window_function,
)
from .expr_kind import ExpressionKind

# Define the union type for valid SELECT expressions
# These types are grouped together because they represent the kinds of expressions
# that can be used in the SELECT clause of a SQL query. This ensures that any expression
# of this type can be safely used in a SELECT statement, as long as the referenced
# columns are present in the table.
#
# Note: Some types may overlap due to inheritance (e.g., Case and Cast inherit
# from Func), but we list them explicitly for clarity and in case sqlglot were
# to change its class structure in the future.
SelectExpression = Union[
    # Literals and basic values
    exp.Null,  # NULL
    exp.Boolean,  # TRUE, FALSE
    exp.Literal,  # 123, 'hello', 45.67
    exp.National,  # N'string' (SQL Server national character string)
    # References
    exp.Column,  # col1, t.col2, db.schema.t.col3
    exp.Identifier,  # Column/table/schema names, aliases
    # Operations
    exp.Binary,  # a + b, a = b, a LIKE '%x%' (arithmetic, comparison, string ops)
    exp.Unary,  # -a, NOT a, +a
    exp.Paren,  # (a + b), ((x))
    # Functions and special functions
    exp.Func,  # ROUND(), SUM(), COUNT(), COALESCE(), SUBSTRING(), any function call
    exp.Case,  # CASE WHEN x > 0 THEN 'positive' ELSE 'negative' END
    exp.Cast,  # CAST('123' AS INT), '123'::INT, TRY_CAST()
    exp.Window,  # SUM(x) OVER (PARTITION BY y ORDER BY z)
    exp.Order,  # ORDER BY clause in OVER()
    exp.Ordered,  # Individual ordering expression with ASC/DESC, NULLS FIRST/LAST
    # Predicates and conditions
    exp.Condition,  # Base class for: Placeholder (?), Parameter ($1), etc.
    exp.Predicate,  # Base class for boolean predicates
    exp.In,  # a IN (1, 2, 3), a NOT IN ('x', 'y')
    exp.Between,  # a BETWEEN 1 AND 10, a NOT BETWEEN x AND y
    # Special constructs
    exp.WithinGroup,  # WITHIN GROUP (ORDER BY x) for ordered-set aggregates
    exp.AtTimeZone,  # timestamp_col AT TIME ZONE 'UTC'
    exp.FromTimeZone,  # FROM_TZ(timestamp, timezone)
    exp.Bracket,  # array[1], map['key'], array[1:3] (array/map access)
    exp.Interval,  # INTERVAL '1 day', INTERVAL '2 hours'
    exp.Comprehension,  # [x * 2 for x in array_col] (DuckDB list comprehension)
    exp.Distinct,  # DISTINCT in SELECT DISTINCT or COUNT(DISTINCT x)
    exp.Filter,  # SUM(amount) FILTER (WHERE status = 'active')
    exp.IgnoreNulls,  # FIRST_VALUE(x) IGNORE NULLS OVER (...)
    exp.RespectNulls,  # FIRST_VALUE(x) RESPECT NULLS OVER (...)
    exp.Introducer,  # _utf8'string', _latin1'text' (MySQL character set)
    exp.JSONPath,  # $.field.subfield in JSON operations
    exp.JSONPathPart,  # Individual JSON path components
    exp.Lambda,  # x -> x * 2, (a, b) -> a + b (Spark SQL lambdas)
    exp.Tuple,  # (1, 2, 3), ROW(a, b), used in VALUES and GROUPING SETS
    exp.DataType,  # INT, VARCHAR(255), DECIMAL(10,2) in CAST expressions
    exp.DataTypeParam,  # The 255 in VARCHAR(255), 10 and 2 in DECIMAL(10,2)
    exp.Star,  # * in COUNT(*) or SELECT *
    exp.Var,  # DAY in INTERVAL '1' DAY, other SQL keywords/variables
]

# Define a tuple of valid types for isinstance checks
SelectExpressionTypes = get_args(SelectExpression)


@dataclass
class TypedSelectExpression:
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
        """Create a TypedSelectExpression from a SQLGlot expression.

        Args:
            expression: A SQLGlot expression to validate and wrap.
            data_type: The data type of the expression's result.
            kind: The expression kind (dimension, measure, or time). If None,
                will be inferred from the expression.
            strict: If True, recursively validates all sub-expressions in the
                expression tree. If False (default), only validates the top-level
                expression.

        Returns:
            A validated TypedSelectExpression.

        Raises:
            ValueError: If the expression or any sub-expression (when strict=True)
                is not compatible with SELECT statements. This prevents SQL
                injection risks and ensures expressions can be safely used in
                SELECT clauses.
        """
        # Validate the top-level expression
        if not isinstance(expression, SelectExpressionTypes):
            msg = (
                "Expected an expression compatible inside a SELECT, "
                f"found {type(expression).__name__}"
            )
            raise TypeCheckError(msg)

        if strict:
            # Recursively validate all sub-expressions
            invalid_nodes = []
            for node in expression.walk():
                if not isinstance(node, SelectExpressionTypes):
                    # Collect invalid nodes with their type names
                    invalid_nodes.append((node, type(node).__name__))

            if invalid_nodes:
                # Create a detailed error message
                # Show up to 5 invalid expressions to avoid overwhelming the error
                sample_size = min(5, len(invalid_nodes))
                invalid_details = []
                for node, type_name in invalid_nodes[:sample_size]:
                    # Get a string representation of the node (truncated if too long)
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

        # Infer the kind from expression
        if kind is None:
            kind = TypedSelectExpression._infer_kind(expression)

        return TypedSelectExpression(
            expression=cast(SelectExpression, expression),
            data_type=data_type,
            kind=kind,
        )

    @classmethod
    def _infer_kind(cls, expression: exp.Expression) -> ExpressionKind:
        if has_window_function(expression):
            return ExpressionKind.WINDOW
        elif has_aggregate_function(expression):
            return ExpressionKind.AGGREGATION
        elif has_column_references(expression):
            return ExpressionKind.COLUMN
        else:
            return ExpressionKind.SCALAR

    def inlinable(self) -> bool:
        """
        Whether the expression can be inlined inside an aggregation
        """
        return self.kind in (ExpressionKind.SCALAR, ExpressionKind.COLUMN)
