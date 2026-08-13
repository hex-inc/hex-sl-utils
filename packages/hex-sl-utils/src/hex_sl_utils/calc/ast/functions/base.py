from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from pydantic import Tag

from hex_sl_utils.calc.ast.args import Args
from hex_sl_utils.calc.ast.base import ExprBase
from hex_sl_utils.datatype import DataType
from hex_sl_utils.dialect.dialect import Dialect
from hex_sl_utils.exception import TypeCheckError
from hex_sl_utils.expr import ExpressionContext

DATETIME_TYPES: set[DataType] = {
    DataType.DATE,
    DataType.TIMESTAMP,
    DataType.TIMESTAMPTZ,
}

if TYPE_CHECKING:
    from hex_sl_utils.calc.visitor import CalcVisitor
    from hex_sl_utils.expr import TypedSelectExpression

T = TypeVar("T")


def _format_types(types: set[DataType]) -> str:
    """Format a set of DataTypes as a readable string."""
    names = sorted(t.name for t in types)
    if len(names) <= 1:
        return names[0] if names else ""
    if len(names) == 2:
        return f"{names[0]} or {names[1]}"
    return ", ".join(names[:-1]) + ", or " + names[-1]


def _expr_sql(arg: TypedSelectExpression) -> str:
    """Return a short SQL representation of an expression for use in error messages."""
    return arg.expression.sql(dialect="duckdb")


class FuncBase(ExprBase):
    args: Args
    fun: str

    @classmethod
    def tag(cls) -> Tag:
        fun = cls.model_fields["fun"].default
        return Tag(f"fun:{fun}")

    def is_agg(self) -> bool:
        return False

    def accept(self, visitor: CalcVisitor[T]) -> T:
        return visitor.visit_func(self)

    def compile(
        self,
        arg_exprs: list[TypedSelectExpression],
        dialect: Dialect,
        context: ExpressionContext,
        tz: str,
    ) -> TypedSelectExpression:
        """
        Compiles the function into a TypedSelectExpression.
        Each subclass should override this method to provide the correct
        SQL function expression, data type, and kind.
        """
        msg = f"Each function must implement its own compile method for {self.fun}."
        raise NotImplementedError(msg)

    def _check_arg_type(
        self,
        arg: TypedSelectExpression,
        expected: set[DataType],
        position: int | None = None,
    ) -> None:
        """Raise TypeCheckError if arg's type is not in expected."""
        if arg.data_type not in expected:
            pos = "" if position is None else f" at position {position}"
            msg = (
                f"{self.fun} expects a {_format_types(expected)} argument"
                f"{pos}, got {arg.data_type.name} "
                f"for expression: {_expr_sql(arg)}"
            )
            raise TypeCheckError(msg)

    def _validate_no_args(self, arg_exprs: list[TypedSelectExpression]) -> None:
        if len(arg_exprs) != 0:
            msg = f"Expected no arguments for {self.fun}"
            raise TypeCheckError(msg)

    def _validate_single_arg(
        self,
        arg_exprs: list[TypedSelectExpression],
        data_type: DataType | set[DataType] | None = None,
    ) -> TypedSelectExpression:
        if len(arg_exprs) != 1:
            msg = f"Expected a single argument for {self.fun}"
            raise TypeCheckError(msg)
        if data_type is not None:
            types = data_type if isinstance(data_type, set) else {data_type}
            self._check_arg_type(arg_exprs[0], types)
        return arg_exprs[0]

    def _validate_variadic_with_type(
        self,
        arg_exprs: list[TypedSelectExpression],
        data_types: DataType | set[DataType],
        allow_empty: bool = True,
        max_args: int | None = None,
    ) -> None:
        if isinstance(data_types, DataType):
            data_types = {data_types}

        if len(arg_exprs) == 0 and not allow_empty:
            msg = f"Expected at least one argument for {self.fun}"
            raise TypeCheckError(msg)
        if max_args is not None and len(arg_exprs) > max_args:
            msg = f"Expected at most {max_args} arguments for {self.fun}"
            raise TypeCheckError(msg)
        for arg in arg_exprs:
            self._check_arg_type(arg, data_types)

    def _validate_variadic_with_same_type(
        self,
        arg_exprs: list[TypedSelectExpression],
        allow_empty: bool = True,
        max_args: int | None = None,
    ) -> None:
        if len(arg_exprs) == 0 and not allow_empty:
            msg = f"Expected at least one argument for {self.fun}"
            raise TypeCheckError(msg)
        if max_args is not None and len(arg_exprs) > max_args:
            msg = f"Expected at most {max_args} arguments for {self.fun}"
            raise TypeCheckError(msg)
        if len(arg_exprs) > 0:
            for arg in arg_exprs[1:]:
                if arg.data_type != arg_exprs[0].data_type:
                    arg_types = ", ".join(f"{arg.data_type}" for arg in arg_exprs)
                    msg = (
                        f"Expected all arguments to have the same type for "
                        f"{self.fun}, got {arg_types}"
                    )
                    raise TypeCheckError(msg)

    def _validate_n_args(
        self,
        arg_exprs: list[TypedSelectExpression],
        n: int,
    ) -> list[TypedSelectExpression]:
        if len(arg_exprs) != n:
            msg = f"Expected {n} arguments for {self.fun}, got {len(arg_exprs)}"
            raise TypeCheckError(msg)
        return arg_exprs

    def _validate_exact_signature(
        self,
        arg_exprs: list[TypedSelectExpression],
        arg_types: list[DataType],
    ) -> list[TypedSelectExpression]:
        if len(arg_exprs) != len(arg_types):
            msg = (
                f"Expected {len(arg_types)} arguments for {self.fun}, "
                f"got {len(arg_exprs)}"
            )
            raise TypeCheckError(msg)
        for i, (arg, expected_type) in enumerate(zip(arg_exprs, arg_types)):
            self._check_arg_type(arg, {expected_type}, position=i)
        return arg_exprs
