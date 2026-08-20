from __future__ import annotations

from collections.abc import Mapping

from hex_sl_utils._vendor.sqlglot import exp, parse_one
from hex_sl_utils.calc.ast.binary import BinaryBase
from hex_sl_utils.calc.ast.column import Column
from hex_sl_utils.calc.ast.functions import FuncBase
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
from hex_sl_utils.datatype import DataType
from hex_sl_utils.dialect.dialect import Dialect
from hex_sl_utils.expr import ExpressionContext, TypedSelectExpression
from hex_sl_utils.expr.expr_substitution import _needs_parens_for_substitution


class CalcToTypedSelectVisitor(CalcVisitor[TypedSelectExpression]):
    def __init__(
        self,
        dialect: Dialect,
        context: ExpressionContext,
        columns: Mapping[str, DataType],
        timezone: str,
        parameters: Mapping[str, DataType] | None = None,
        substitutions: Mapping[str, TypedSelectExpression] | None = None,
        skip_mangle: bool | list[str] | None = None,
    ) -> None:
        self.columns = columns
        self.dialect = dialect
        self.context = context
        self.timezone = timezone
        self.parameters = dict(parameters or {})
        self.substitutions = dict(substitutions or {})
        self.skip_mangle = skip_mangle or []

    def visit_literal_number(self, literal: LiteralNumber) -> TypedSelectExpression:
        return literal.compile(self.dialect)

    def visit_literal_string(self, literal: LiteralString) -> TypedSelectExpression:
        return literal.compile(self.dialect)

    def visit_literal_bool(self, literal: LiteralBool) -> TypedSelectExpression:
        return literal.compile(self.dialect)

    def visit_literal_timestamp(
        self, literal: LiteralTimestamp
    ) -> TypedSelectExpression:
        return literal.compile(self.dialect)

    def visit_literal_date(self, literal: LiteralDate) -> TypedSelectExpression:
        return literal.compile(self.dialect)

    def visit_literal_null(self, literal: LiteralNull) -> TypedSelectExpression:
        return literal.compile(self.dialect)

    def visit_column(self, column: Column) -> TypedSelectExpression:
        return column.compile(
            self.columns, self.dialect, self.substitutions, self.skip_mangle
        )

    def visit_parameter(self, parameter: Parameter) -> TypedSelectExpression:
        return parameter.compile(self.parameters)

    def visit_unary(self, unary: UnaryBase) -> TypedSelectExpression:
        arg_expr = unary.arg.root.accept(self)
        return unary.compile(arg_expr, self.dialect)

    def visit_binary(self, binary: BinaryBase) -> TypedSelectExpression:
        left_expr = binary.lhs.root.accept(self)
        right_expr = binary.rhs.root.accept(self)
        return binary.compile(left_expr, right_expr, self.dialect, self.timezone)

    def visit_func(self, func: FuncBase) -> TypedSelectExpression:
        arg_exprs = [arg.root.accept(self) for arg in func.args.root]
        typed_select_expr = func.compile(
            arg_exprs, self.dialect, self.context, self.timezone
        )
        return typed_select_expr

    def visit_sql_expression(self, sql_expr: SqlExpression) -> TypedSelectExpression:
        sqlglot_expr = parse_one(sql_expr.sql, dialect=self.dialect.sqlglot_dialect())

        # Resolve column references by applying substitutions (inlining dimension
        # calc expressions), performing schema lookups, and applying name mangling
        def resolve_column_reference(node: exp.Expression) -> exp.Expression:
            if isinstance(node, exp.Column):
                column = Column(
                    name=node.name, qualifiers=(node.table,) if node.table else ()
                )
                result_expr = self.visit_column(column).expression

                # Wrap in parens if needed to avoid operator precedence issues
                if _needs_parens_for_substitution(result_expr):
                    result_expr = exp.Paren(this=result_expr)

                return result_expr
            return node

        # Apply column resolution to all column references in the SQL expression
        resolved_expr = sqlglot_expr.transform(resolve_column_reference)

        # Then resolve any _HEXSL_CALC placeholders
        resolved_expr = self.dialect.resolve_calc_placeholders(
            resolved_expr,
            columns=self.columns,
            timezone=self.timezone,
            context=self.context,
            parameters=self.parameters,
            substitutions=self.substitutions,
        )

        return TypedSelectExpression.from_sqlglot(
            resolved_expr, sql_expr.data_type, strict=True
        )
