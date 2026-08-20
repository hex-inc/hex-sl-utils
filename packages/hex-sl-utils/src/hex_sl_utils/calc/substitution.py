from __future__ import annotations

from typing import TYPE_CHECKING

from hex_sl_utils._vendor.sqlglot import exp, parse_one
from hex_sl_utils.calc.ast.args import Args
from hex_sl_utils.calc.ast.base import ExprBase
from hex_sl_utils.calc.ast.binary.base import BinaryBase
from hex_sl_utils.calc.ast.column import Column
from hex_sl_utils.calc.ast.functions.base import FuncBase
from hex_sl_utils.calc.ast.literals import (
    LiteralBool,
    LiteralDate,
    LiteralNull,
    LiteralNumber,
    LiteralString,
    LiteralTimestamp,
)
from hex_sl_utils.calc.ast.parameter import Parameter
from hex_sl_utils.calc.ast.sql_expression import SqlExpression
from hex_sl_utils.calc.ast.unary import UnaryBase
from hex_sl_utils.calc.visitor import CalcVisitor

if TYPE_CHECKING:
    from hex_sl_utils.dialect.dialect import Dialect


class ColumnSubstitutionVisitor(CalcVisitor[ExprBase]):
    def __init__(
        self,
        column_mapping: dict[str, ExprBase],
        dialect: Dialect | None = None,
    ) -> None:
        self.column_mapping = column_mapping
        self.dialect = dialect

    def visit_literal_number(self, literal: LiteralNumber) -> ExprBase:
        return literal

    def visit_literal_string(self, literal: LiteralString) -> ExprBase:
        return literal

    def visit_literal_bool(self, literal: LiteralBool) -> ExprBase:
        return literal

    def visit_literal_timestamp(self, literal: LiteralTimestamp) -> ExprBase:
        return literal

    def visit_literal_date(self, literal: LiteralDate) -> ExprBase:
        return literal

    def visit_literal_null(self, literal: LiteralNull) -> ExprBase:
        return literal

    def visit_column(self, column: Column) -> ExprBase:
        # Perform the substitution
        return self.column_mapping.get(column.name, column)

    def visit_parameter(self, parameter: Parameter) -> ExprBase:
        return parameter

    def visit_binary(self, binary: BinaryBase) -> ExprBase:
        binary = binary.model_copy()
        binary.lhs = binary.lhs.root.accept(self).to_expr()
        binary.rhs = binary.rhs.root.accept(self).to_expr()
        return binary

    def visit_unary(self, unary: UnaryBase) -> ExprBase:
        unary = unary.model_copy()
        unary.arg = unary.arg.root.accept(self).to_expr()
        return unary

    def visit_func(self, func: FuncBase) -> ExprBase:
        func = func.model_copy()
        # Rebind a fresh Args instead of mutating in place: the shallow copy above
        # aliases `args`, so writing `func.args.root` would corrupt the input node
        # (which may be shared, e.g. via the parse_calc_expression cache).
        func.args = Args([arg.root.accept(self).to_expr() for arg in func.args.root])
        return func

    def visit_sql_expression(self, sql_expr: SqlExpression) -> ExprBase:
        if not self.column_mapping:
            # No substitutions needed
            return sql_expr

        if not self.dialect:
            msg = "dialect is required for SqlExpression substitution"
            raise ValueError(msg)

        # Parse the SQL with the dialect
        sqlglot_expr = parse_one(sql_expr.sql, dialect=self.dialect.sqlglot_dialect())

        # Transform column nodes and existing _hexsl_calc placeholders
        def transform_nodes(node: exp.Expression) -> exp.Expression:
            from hex_sl_utils.calc.visitor import (
                HEXSL_CALC_FN_NAME,
                _extract_hexsl_calc_string,
            )

            # Handle existing _hexsl_calc placeholders
            if calc_str := _extract_hexsl_calc_string(node):
                # Parse the calc expression from JSON
                from hex_sl_utils.calc.ast.expr import CalcExpr

                calc_expr = CalcExpr.model_validate_json(calc_str)

                # Apply substitutions to the calc expression recursively
                # dialect is guaranteed to be non-None here due to check above
                assert self.dialect is not None
                substituted_calc = calc_expr.substitute(
                    substitutions=self.column_mapping, dialect=self.dialect
                )

                # Return updated placeholder with substituted calc as JSON
                return exp.Anonymous(
                    this=HEXSL_CALC_FN_NAME,
                    expressions=[
                        exp.Literal.string(
                            substituted_calc.model_dump_json(by_alias=True)
                        )
                    ],
                )

            # Handle regular column references
            elif isinstance(node, exp.Column) and not node.table:
                col_name = node.name
                if col_name in self.column_mapping:
                    # Get the calc expression as JSON
                    subst_expr = self.column_mapping[col_name]
                    calc_json = subst_expr.to_expr().model_dump_json(by_alias=True)

                    # Create _hexsl_calc function placeholder with calc JSON
                    return exp.Anonymous(
                        this=HEXSL_CALC_FN_NAME,
                        expressions=[exp.Literal.string(calc_json)],
                    )

            return node

        # Transform the expression
        transformed = sqlglot_expr.transform(transform_nodes)

        # Create new SqlExpression with transformed SQL
        return SqlExpression(
            sql=transformed.sql(dialect=self.dialect.sqlglot_dialect()),
            data_type=sql_expr.data_type,
        )


class QualifyColumnsVisitor(ColumnSubstitutionVisitor):
    """Add dataset qualifiers to unqualified Column nodes."""

    def __init__(self, dataset: str) -> None:
        super().__init__({})
        self.dataset = dataset

    def visit_column(self, column: Column) -> ExprBase:
        if not column.qualifiers:
            return Column(name=column.name, qualifiers=(self.dataset,))
        return column
