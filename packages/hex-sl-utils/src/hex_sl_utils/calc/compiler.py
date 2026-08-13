from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Union

from hex_sl._vendor.sqlglot import parse_one
from hex_sl.calc.ast.binary import BinaryBase
from hex_sl.calc.ast.column import Column
from hex_sl.calc.ast.functions import FuncBase
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
from hex_sl.datatype import DataType
from hex_sl.expr import (
    ExpressionContext,
    TypedSelectExpression,
)
from hex_sl.schema import Schema

if TYPE_CHECKING:
    from hex_sl.dialect.base import HexSLDialect


class CalcToTypedSelectVisitor(CalcVisitor[TypedSelectExpression]):
    def __init__(
        self,
        dialect: HexSLDialect,
        context: ExpressionContext,
        schema: Schema,
        timezone: str,
        parameters: Optional[dict[str, DataType]] = None,
        substitutions: Optional[dict[str, TypedSelectExpression]] = None,
        skip_mangle: Union[bool, list[str], None] = None,
    ) -> None:
        self.schema = schema
        self.dialect = dialect
        self.context = context
        self.timezone = timezone
        self.parameters = parameters or {}
        self.substitutions = substitutions or {}
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
            self.schema, self.dialect, self.substitutions, self.skip_mangle
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
        from hex_sl._vendor.sqlglot import exp
        from hex_sl.calc.ast.column import Column

        sqlglot_expr = parse_one(sql_expr.sql, dialect=self.dialect.sqlglot_dialect())

        # Resolve column references by applying substitutions (inlining dimension
        # calc expressions), performing schema lookups, and applying name mangling
        def resolve_column_reference(node: exp.Expression) -> exp.Expression:
            if isinstance(node, exp.Column):
                from hex_sl.expr import _needs_parens_for_substitution

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
        resolved_expr = self.dialect.resolve_hexsl_calc_placeholders(
            resolved_expr,
            schema=self.schema,
            timezone=self.timezone,
            context=self.context,
            parameters=self.parameters,
            substitutions=self.substitutions,
        )

        return TypedSelectExpression.from_sqlglot(
            resolved_expr, sql_expr.data_type, strict=True
        )
