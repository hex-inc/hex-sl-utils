from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic, TypeVar

from hex_sl_utils.calc.ast.base import QualifiedColumnRef
from hex_sl_utils.calc.ast.parameter import Parameter

if TYPE_CHECKING:
    from hex_sl_utils.calc.ast.base import ExprBase
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
    from hex_sl_utils.calc.ast.sql_expression import SqlExpression
    from hex_sl_utils.calc.ast.unary import UnaryBase
    from hex_sl_utils.calc.protocols import CalcDialect

# Define a type variable for the return type of the visitor methods
T = TypeVar("T")

# Constant for the hexsl calc placeholder function name
HEXSL_CALC_FN_NAME = "_HEXSL_CALC"


def _extract_hexsl_calc_string(node: object) -> str | None:
    """Extract the calc expression string from a node if it's a _hexsl_calc function.

    Args:
        node: A sqlglot expression node

    Returns:
        The calc expression string if node is _hexsl_calc, None otherwise

    Raises:
        ValueError: If the node is _hexsl_calc but doesn't have exactly one string
            literal argument
    """
    from hex_sl_utils._vendor.sqlglot import exp

    if not (
        isinstance(node, exp.Anonymous) and node.this.upper() == HEXSL_CALC_FN_NAME
    ):
        return None

    if not node.expressions:
        msg = f"{HEXSL_CALC_FN_NAME}() requires exactly one string literal argument"
        raise ValueError(msg)

    arg = node.expressions[0]
    if isinstance(arg, exp.Literal):
        return str(arg.this)
    else:
        msg = (
            f"{HEXSL_CALC_FN_NAME}() requires a string literal argument. "
            f"Got {type(arg).__name__}: {arg}"
        )
        raise ValueError(msg)  # noqa: TRY004 - preserve the HexSL error contract


class CalcVisitor(ABC, Generic[T]):
    """
    Abstract base class for visitors that can traverse CalcExpr AST nodes.

    This class uses the visitor pattern to define operations that can be
    performed on CalcExpr nodes without modifying the nodes themselves.

    Type variable T represents the return type of the visitor methods.
    """

    @abstractmethod
    def visit_literal_number(self, literal: LiteralNumber) -> T:
        pass

    @abstractmethod
    def visit_literal_string(self, literal: LiteralString) -> T:
        pass

    @abstractmethod
    def visit_literal_bool(self, literal: LiteralBool) -> T:
        pass

    @abstractmethod
    def visit_literal_timestamp(self, literal: LiteralTimestamp) -> T:
        pass

    @abstractmethod
    def visit_literal_date(self, literal: LiteralDate) -> T:
        pass

    @abstractmethod
    def visit_literal_null(self, literal: LiteralNull) -> T:
        pass

    @abstractmethod
    def visit_column(self, column: Column) -> T:
        pass

    @abstractmethod
    def visit_parameter(self, parameter: Parameter) -> T:
        pass

    @abstractmethod
    def visit_binary(self, binary: BinaryBase) -> T:
        pass

    @abstractmethod
    def visit_unary(self, unary: UnaryBase) -> T:
        pass

    @abstractmethod
    def visit_func(self, func: FuncBase) -> T:
        pass

    @abstractmethod
    def visit_sql_expression(self, sql_expr: SqlExpression) -> T:
        pass

    def visit(self, expr: ExprBase) -> T:
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
        from hex_sl_utils.calc.ast.sql_expression import SqlExpression
        from hex_sl_utils.calc.ast.unary import UnaryBase

        if isinstance(expr, LiteralNumber):
            return self.visit_literal_number(expr)
        elif isinstance(expr, LiteralString):
            return self.visit_literal_string(expr)
        elif isinstance(expr, LiteralBool):
            return self.visit_literal_bool(expr)
        elif isinstance(expr, LiteralTimestamp):
            return self.visit_literal_timestamp(expr)
        elif isinstance(expr, LiteralDate):
            return self.visit_literal_date(expr)
        elif isinstance(expr, LiteralNull):
            return self.visit_literal_null(expr)
        elif isinstance(expr, Column):
            return self.visit_column(expr)
        elif isinstance(expr, Parameter):
            return self.visit_parameter(expr)
        elif isinstance(expr, BinaryBase):
            return self.visit_binary(expr)
        elif isinstance(expr, UnaryBase):
            return self.visit_unary(expr)
        elif isinstance(expr, FuncBase):
            return self.visit_func(expr)
        elif isinstance(expr, SqlExpression):
            return self.visit_sql_expression(expr)
        else:
            msg = f"Visit method for {type(expr).__name__} is not implemented."
            raise NotImplementedError(msg)


class CalcToStringVisitor(CalcVisitor[str]):
    def visit_literal_number(self, literal: LiteralNumber) -> str:
        if (
            isinstance(literal.number_value, float)
            and literal.number_value.is_integer()
        ):
            return str(int(literal.number_value))
        return str(literal.number_value)

    def visit_literal_string(self, literal: LiteralString) -> str:
        return f'"{literal.str_value}"'

    def visit_literal_bool(self, literal: LiteralBool) -> str:
        return "true" if literal.bool_value else "false"

    def visit_literal_timestamp(self, literal: LiteralTimestamp) -> str:
        if literal.timestamp_value.microsecond == 0:
            return f't"{literal.timestamp_value.isoformat(timespec="seconds")}"'
        else:
            return f't"{literal.timestamp_value.isoformat(timespec="milliseconds")}"'

    def visit_literal_date(self, literal: LiteralDate) -> str:
        return f'd"{literal.date_value.isoformat()}"'

    def visit_literal_null(self, literal: LiteralNull) -> str:
        return "null"

    def visit_column(self, column: Column) -> str:
        def format_part(part: str) -> str:
            if part.isidentifier() and part.lower() not in {
                "true",
                "false",
                "null",
            }:
                return part
            return f"`{part}`"

        # Format qualifiers and column name
        parts = [format_part(q) for q in column.qualifiers]
        parts.append(format_part(column.name))

        return ".".join(parts)

    def visit_parameter(self, parameter: Parameter) -> str:
        return f"{{{{{parameter.parameter}}}}}"

    def visit_binary(self, binary: BinaryBase) -> str:
        binary_op = getattr(binary, "binary", None)
        if not binary_op or not isinstance(binary_op, str):
            msg = "Subclasses must define 'binary' attribute"
            raise AttributeError(msg)
        return (
            f"({binary.lhs.root.accept(self)} "
            f"{binary_op} "
            f"{binary.rhs.root.accept(self)})"
        )

    def visit_unary(self, unary: UnaryBase) -> str:
        unary_op = getattr(unary, "unary", None)
        if not unary_op or not isinstance(unary_op, str):
            msg = "Subclasses must define 'unary' attribute"
            raise AttributeError(msg)
        return f"({unary_op}{unary.arg.root.accept(self)})"

    def visit_func(self, func: FuncBase) -> str:
        fun = getattr(func, "fun", None)
        if not fun or not isinstance(fun, str):
            msg = "Subclasses must define 'fun' attribute"
            raise AttributeError(msg)
        args_str = ", ".join(arg.root.accept(self) for arg in func.args.root)
        return f"{fun}({args_str})"

    def visit_sql_expression(self, sql_expr: SqlExpression) -> str:
        # Return a readable representation. This isn't parsable
        # yet.
        return f"SQL({sql_expr.sql})"


class CollectColumnsVisitor(CalcVisitor[set[str]]):
    def __init__(self, dialect: CalcDialect) -> None:
        self.dialect = dialect

    def visit_literal_string(self, literal: LiteralString) -> set[str]:
        return set()

    def visit_literal_bool(self, literal: LiteralBool) -> set[str]:
        return set()

    def visit_literal_timestamp(self, literal: LiteralTimestamp) -> set[str]:
        return set()

    def visit_literal_date(self, literal: LiteralDate) -> set[str]:
        return set()

    def visit_literal_null(self, literal: LiteralNull) -> set[str]:
        return set()

    def visit_literal_number(self, literal: LiteralNumber) -> set[str]:
        return set()

    def visit_binary(self, binary: BinaryBase) -> set[str]:
        cols_rhs: set[str] = binary.rhs.root.accept(self)
        cols_lhs: set[str] = binary.lhs.root.accept(self)
        cols_rhs.update(cols_lhs)
        return cols_rhs

    def visit_unary(self, unary: UnaryBase) -> set[str]:
        result: set[str] = unary.arg.root.accept(self)
        return result

    def visit_func(self, func: FuncBase) -> set[str]:
        cols = set()
        for arg in func.args.root:
            # I haven't been able to figure out why mypy
            # is unhappy with this
            col_set: set[str] = arg.root.accept(self)
            cols.update(col_set)
        return cols

    def visit_column(self, column: Column) -> set[str]:
        return {column.name}

    def visit_parameter(self, parameter: Parameter) -> set[str]:
        return set()

    def visit_sql_expression(self, sql_expr: SqlExpression) -> set[str]:
        from hex_sl_utils._vendor.sqlglot import exp, parse_one

        # Use the dialect provided to the visitor
        sqlglot_expr = parse_one(sql_expr.sql, dialect=self.dialect.sqlglot_dialect())

        columns = set()

        for node in sqlglot_expr.walk():
            if calc_str := _extract_hexsl_calc_string(node):
                from hex_sl_utils.calc.ast.expr import CalcExpr

                calc_expr = CalcExpr.model_validate_json(calc_str)
                # Get columns from the calc expression
                columns.update(calc_expr.get_unqualified_columns(self.dialect))
            elif isinstance(node, exp.Column) and not node.table:
                columns.add(node.name)

        return columns


class CollectQualifiedColumnsVisitor(CalcVisitor[set[QualifiedColumnRef]]):
    """Visitor that collects (qualifiers, column_name) tuples from calc expressions."""

    def __init__(self, dialect: CalcDialect) -> None:
        self.dialect = dialect

    def visit_literal_string(self, literal: LiteralString) -> set[QualifiedColumnRef]:
        return set()

    def visit_literal_bool(self, literal: LiteralBool) -> set[QualifiedColumnRef]:
        return set()

    def visit_literal_timestamp(
        self, literal: LiteralTimestamp
    ) -> set[QualifiedColumnRef]:
        return set()

    def visit_literal_date(self, literal: LiteralDate) -> set[QualifiedColumnRef]:
        return set()

    def visit_literal_null(self, literal: LiteralNull) -> set[QualifiedColumnRef]:
        return set()

    def visit_literal_number(self, literal: LiteralNumber) -> set[QualifiedColumnRef]:
        return set()

    def visit_binary(self, binary: BinaryBase) -> set[QualifiedColumnRef]:
        cols_rhs: set[QualifiedColumnRef] = binary.rhs.root.accept(self)
        cols_lhs: set[QualifiedColumnRef] = binary.lhs.root.accept(self)
        cols_rhs.update(cols_lhs)
        return cols_rhs

    def visit_unary(self, unary: UnaryBase) -> set[QualifiedColumnRef]:
        result: set[QualifiedColumnRef] = unary.arg.root.accept(self)
        return result

    def visit_func(self, func: FuncBase) -> set[QualifiedColumnRef]:
        cols = set()
        for arg in func.args.root:
            col_set: set[QualifiedColumnRef] = arg.root.accept(self)
            cols.update(col_set)
        return cols

    def visit_column(self, column: Column) -> set[QualifiedColumnRef]:
        return {(column.qualifiers, column.name)}

    def visit_parameter(self, parameter: Parameter) -> set[QualifiedColumnRef]:
        return set()

    def visit_sql_expression(self, sql_expr: SqlExpression) -> set[QualifiedColumnRef]:
        from hex_sl_utils._vendor.sqlglot import exp, parse_one

        # Use the dialect provided to the visitor
        sqlglot_expr = parse_one(sql_expr.sql, dialect=self.dialect.sqlglot_dialect())

        refs = set()

        for node in sqlglot_expr.walk():
            if calc_str := _extract_hexsl_calc_string(node):
                from hex_sl_utils.calc.ast.expr import CalcExpr

                calc_expr = CalcExpr.model_validate_json(calc_str)
                # Get all columns (qualified and unqualified) from the calc expression
                all_cols = calc_expr.get_all_columns(self.dialect)
                for qualifiers, col in all_cols:
                    refs.add((qualifiers, col))
            elif isinstance(node, exp.Column):
                if node.table:
                    refs.add(((node.table,), node.name))
                else:
                    refs.add(((), node.name))

        return refs


class AnyAggregateFunctionVisitor(CalcVisitor[bool]):
    def __init__(self, dialect: CalcDialect) -> None:
        """Initialize with the SQL dialect for parsing SQL expressions."""
        self.dialect = dialect

    def visit_literal_string(self, literal: LiteralString) -> bool:
        return False

    def visit_literal_bool(self, literal: LiteralBool) -> bool:
        return False

    def visit_literal_timestamp(self, literal: LiteralTimestamp) -> bool:
        return False

    def visit_literal_date(self, literal: LiteralDate) -> bool:
        return False

    def visit_literal_null(self, literal: LiteralNull) -> bool:
        return False

    def visit_literal_number(self, literal: LiteralNumber) -> bool:
        return False

    def visit_binary(self, binary: BinaryBase) -> bool:
        agg_rhs: bool = binary.rhs.root.accept(self)
        agg_lhs: bool = binary.lhs.root.accept(self)
        return agg_rhs or agg_lhs

    def visit_unary(self, unary: UnaryBase) -> bool:
        result: bool = unary.arg.root.accept(self)
        return result

    def visit_func(self, func: FuncBase) -> bool:
        is_agg = func.is_agg()
        for arg in func.args.root:
            arg_is_agg: bool = arg.root.accept(self)
            is_agg = is_agg or arg_is_agg
        return is_agg

    def visit_column(self, column: Column) -> bool:
        return False

    def visit_parameter(self, parameter: Parameter) -> bool:
        return False

    def visit_sql_expression(self, sql_expr: SqlExpression) -> bool:
        from hex_sl_utils._vendor.sqlglot import parse_one
        from hex_sl_utils.calc.compiled import has_aggregate_function

        # Use the dialect provided to the visitor
        sqlglot_expr = parse_one(sql_expr.sql, dialect=self.dialect.sqlglot_dialect())

        # Check for aggregates in the SQL
        if has_aggregate_function(sqlglot_expr):
            return True

        # Also check inside _hexsl_calc placeholders
        for node in sqlglot_expr.walk():
            if calc_str := _extract_hexsl_calc_string(node):
                from hex_sl_utils.calc.ast.expr import CalcExpr

                calc_expr = CalcExpr.model_validate_json(calc_str)
                # Check if the calc expression has aggregates
                if calc_expr.has_aggregation(self.dialect):
                    return True

        return False
