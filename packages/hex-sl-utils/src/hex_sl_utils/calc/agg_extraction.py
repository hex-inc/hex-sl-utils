from __future__ import annotations

from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from hex_sl.dialect.base import HexSLDialect

from hex_sl.calc.ast.args import Args
from hex_sl.calc.ast.base import ExprBase
from hex_sl.calc.ast.binary.base import BinaryBase
from hex_sl.calc.ast.column import Column
from hex_sl.calc.ast.expr import CalcExpr
from hex_sl.calc.ast.functions.aggs import FuncAggBase
from hex_sl.calc.ast.functions.base import FuncBase
from hex_sl.calc.ast.literals import (
    LiteralBool,
    LiteralDate,
    LiteralNull,
    LiteralNumber,
    LiteralString,
    LiteralTimestamp,
)
from hex_sl.calc.ast.parameter import Parameter
from hex_sl.calc.ast.sql_expression import SqlExpression
from hex_sl.calc.ast.unary import UnaryBase
from hex_sl.calc.visitor import CalcVisitor

PRIVATE_AGG_PREFIX = "_agg_"

AggExpr = Union[FuncAggBase, SqlExpression]


class AggregateExtractionVisitor(CalcVisitor[tuple[ExprBase, dict[str, AggExpr]]]):
    """
    A visitor that extracts aggregate function expressions and replaces them with
    column references.

    This visitor traverses an expression tree, identifies aggregate functions (including
    SQL expressions containing aggregates), and replaces them with column references.
    Along with the updated expression tree, it returns a mapping from the new column
    names to the original aggregate expressions.
    """

    def __init__(self, dialect: HexSLDialect) -> None:
        """
        Initialize the visitor.

        Args:
            dialect: The SQL dialect to use for parsing SQL expressions.
        """
        self.next_column_index = 0
        self.dialect = dialect

    def _create_column_for_agg(
        self, agg_expr: AggExpr
    ) -> tuple[ExprBase, dict[str, AggExpr]]:
        """
        Create a column reference for an aggregate expression.

        Args:
            agg_expr: The aggregate expression (either FuncAggBase or
                SqlExpression with aggregates)

        Returns:
            A column reference that should replace the aggregate expression
        """
        # Create a new column reference
        column_name = f"{PRIVATE_AGG_PREFIX}{self.next_column_index}"
        self.next_column_index += 1

        column = Column(name=column_name)
        return column, {column_name: agg_expr}

    def visit_literal_number(
        self, literal: LiteralNumber
    ) -> tuple[ExprBase, dict[str, AggExpr]]:
        return literal, {}

    def visit_literal_string(
        self, literal: LiteralString
    ) -> tuple[ExprBase, dict[str, AggExpr]]:
        return literal, {}

    def visit_literal_bool(
        self, literal: LiteralBool
    ) -> tuple[ExprBase, dict[str, AggExpr]]:
        return literal, {}

    def visit_literal_timestamp(
        self, literal: LiteralTimestamp
    ) -> tuple[ExprBase, dict[str, AggExpr]]:
        return literal, {}

    def visit_literal_date(
        self, literal: LiteralDate
    ) -> tuple[ExprBase, dict[str, AggExpr]]:
        return literal, {}

    def visit_literal_null(
        self, literal: LiteralNull
    ) -> tuple[ExprBase, dict[str, AggExpr]]:
        return literal, {}

    def visit_column(self, column: Column) -> tuple[ExprBase, dict[str, AggExpr]]:
        return column, {}

    def visit_parameter(
        self, parameter: Parameter
    ) -> tuple[ExprBase, dict[str, AggExpr]]:
        return parameter, {}

    def visit_binary(self, binary: BinaryBase) -> tuple[ExprBase, dict[str, AggExpr]]:
        # Process the left and right sides first
        binary = binary.model_copy()
        new_lhs, lhs_column_to_agg = binary.lhs.root.accept(self)
        new_rhs, rhs_column_to_agg = binary.rhs.root.accept(self)
        binary.lhs = new_lhs.to_expr()
        binary.rhs = new_rhs.to_expr()
        return binary, {**lhs_column_to_agg, **rhs_column_to_agg}

    def visit_unary(self, unary: UnaryBase) -> tuple[ExprBase, dict[str, AggExpr]]:
        # Process the argument first
        unary = unary.model_copy()
        new_arg, arg_column_to_agg = unary.arg.root.accept(self)
        unary.arg = new_arg.to_expr()
        return unary, arg_column_to_agg

    def visit_func(self, func: FuncBase) -> tuple[ExprBase, dict[str, AggExpr]]:
        if isinstance(func, FuncAggBase):
            # Replace the entire function with a new column reference.
            # Agg functions may not nest, so we don't need to process their arguments.
            return self._create_column_for_agg(func)
        else:
            # Not an aggregate function, just process its arguments
            func = func.model_copy()
            arg_column_to_agg: dict[str, AggExpr] = {}
            new_args: list[CalcExpr] = []

            for arg in func.args.root:
                new_arg, inner_arg_to_aggs = arg.root.accept(self)
                arg_column_to_agg.update(**inner_arg_to_aggs)
                new_args.append(new_arg.to_expr())

            # Rebind a fresh Args instead of mutating in place: the shallow copy
            # above aliases `args`, so writing `func.args.root` would corrupt the
            # input node (which may be shared, e.g. via the parse_calc_expression
            # cache).
            func.args = Args(new_args)
            return func, arg_column_to_agg

    def visit_sql_expression(
        self, sql_expr: SqlExpression
    ) -> tuple[ExprBase, dict[str, AggExpr]]:
        # Check if the SQL expression contains aggregate functions
        from hex_sl._vendor.sqlglot import parse_one
        from hex_sl.expr import has_aggregate_function

        sqlglot_expr = parse_one(sql_expr.sql, dialect=self.dialect.sqlglot_dialect())

        # If the SQL expression contains aggregate functions, we need to treat
        # the entire SQL expression as an aggregate that needs extraction
        if has_aggregate_function(sqlglot_expr):
            # The SQL expression itself is the aggregate - extract it
            return self._create_column_for_agg(sql_expr)
        else:
            # SQL expression doesn't contain aggregates, return as-is
            return sql_expr, {}
