# pyright: reportCallIssue=false, reportIncompatibleVariableOverride=false
from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import Field

from hex_sl_utils._vendor.sqlglot import exp
from hex_sl_utils.calc.ast.binary.base import BinaryBase
from hex_sl_utils.calc.compiled import (
    ExpressionContext,
    ExpressionKind,
    TypedSelectExpression,
)
from hex_sl_utils.calc.errors import TypeCheckError
from hex_sl_utils.calc.parentheses import parens_if_needed
from hex_sl_utils.calc.protocols import CalcDialect
from hex_sl_utils.types import DataType

if TYPE_CHECKING:
    # This import seems to be needed to help mypy follow that the BinaryBase
    # lhs/rhs CalcExpr properties are available in child classes
    from hex_sl_utils.calc.ast import CalcExpr  # noqa: F401


class BinaryComparisonBase(BinaryBase):
    """
    Base class for binary comparison operators
    """

    def _validate_comparison_operator_arg_types(
        self, left_type: DataType, right_type: DataType
    ) -> None:
        ts_types = (DataType.TIMESTAMP_NAIVE, DataType.TIMESTAMP_TZ, DataType.DATE)
        if left_type in ts_types and right_type in ts_types:
            # mixing timestamp, timestamptz, and date is allowed
            return
        elif left_type != right_type:
            msg = (
                f"Unsupported binary operator {self.get_op()} for data types "
                f"{left_type} and {right_type}"
            )
            raise TypeCheckError(msg)

    @classmethod
    def _unify_types(
        cls,
        left_expr: TypedSelectExpression,
        right_expr: TypedSelectExpression,
        dialect: CalcDialect,
        tz: str,
    ) -> tuple[TypedSelectExpression, TypedSelectExpression]:
        # Cast down dates to timestamps/timestamptz
        if left_expr.data_type == DataType.DATE:
            if right_expr.data_type == DataType.TIMESTAMP_NAIVE:
                left_expr = dialect.cast_date_to_timestamp(left_expr)
            elif right_expr.data_type == DataType.TIMESTAMP_TZ:
                left_expr = dialect.cast_date_to_timestamptz(left_expr, tz)

        if right_expr.data_type == DataType.DATE:
            if left_expr.data_type == DataType.TIMESTAMP_NAIVE:
                right_expr = dialect.cast_date_to_timestamp(right_expr)
            elif left_expr.data_type == DataType.TIMESTAMP_TZ:
                right_expr = dialect.cast_date_to_timestamptz(right_expr, tz)

        # Unify timestamp and timestamptz
        if (
            left_expr.data_type == DataType.TIMESTAMP_NAIVE
            and right_expr.data_type == DataType.TIMESTAMP_TZ
        ):
            left_expr = dialect.at_timezone(left_expr, tz)
        elif (
            left_expr.data_type == DataType.TIMESTAMP_TZ
            and right_expr.data_type == DataType.TIMESTAMP_NAIVE
        ):
            right_expr = dialect.at_timezone(right_expr, tz)

        return left_expr, right_expr

    def compile(
        self,
        left_expr: TypedSelectExpression,
        right_expr: TypedSelectExpression,
        dialect: CalcDialect,
        timezone: str,
    ) -> TypedSelectExpression:
        # For cases like booleans in mssql, we need to wrap the expression as if
        # it were at the top-level before applying comparison binary operators
        left_expr = dialect.wrap_expression_for_context(
            left_expr, ExpressionContext.PROJECTION
        )
        right_expr = dialect.wrap_expression_for_context(
            right_expr, ExpressionContext.PROJECTION
        )

        self._validate_comparison_operator_arg_types(
            left_expr.data_type, right_expr.data_type
        )
        kind = ExpressionKind._validate_infer_kind([left_expr.kind, right_expr.kind])
        return self.perform_compile(left_expr, right_expr, dialect, kind, timezone)

    @classmethod
    def perform_compile(
        cls,
        left_expr: TypedSelectExpression,
        right_expr: TypedSelectExpression,
        dialect: CalcDialect,
        kind: ExpressionKind,
        timezone: str,
    ) -> TypedSelectExpression:
        msg = "perform_compile is not implemented"
        raise NotImplementedError(msg)


class BinaryLess(BinaryComparisonBase):
    binary: Literal["<"] = Field(
        default="<",
        description="Binary less than operator, as in 2 < 3 = true",
        title="binary-less-op",
    )

    @classmethod
    def perform_compile(
        cls,
        left_expr: TypedSelectExpression,
        right_expr: TypedSelectExpression,
        dialect: CalcDialect,
        kind: ExpressionKind,
        timezone: str,
    ) -> TypedSelectExpression:
        left_expr, right_expr = cls._unify_types(
            left_expr, right_expr, dialect, timezone
        )
        # Wrap operands in parentheses if needed based on precedence
        left = parens_if_needed(left_expr.expression, "<", operand_type="left")
        right = parens_if_needed(right_expr.expression, "<", operand_type="right")

        lt_expr = exp.LT(this=left, expression=right)
        return TypedSelectExpression.from_sqlglot(lt_expr, DataType.BOOLEAN, kind)


class BinaryLessEqual(BinaryComparisonBase):
    binary: Literal["<="] = Field(
        default="<=",
        description="Binary less than or equal operator, as in 3 <= 3 = true",
        title="binary-less-equal-op",
    )

    @classmethod
    def perform_compile(
        cls,
        left_expr: TypedSelectExpression,
        right_expr: TypedSelectExpression,
        dialect: CalcDialect,
        kind: ExpressionKind,
        timezone: str,
    ) -> TypedSelectExpression:
        left_expr, right_expr = cls._unify_types(
            left_expr, right_expr, dialect, timezone
        )
        # Wrap operands in parentheses if needed based on precedence
        left = parens_if_needed(left_expr.expression, "<=", operand_type="left")
        right = parens_if_needed(right_expr.expression, "<=", operand_type="right")

        lte_expr = exp.LTE(this=left, expression=right)
        return TypedSelectExpression.from_sqlglot(lte_expr, DataType.BOOLEAN, kind)


class BinaryGreater(BinaryComparisonBase):
    binary: Literal[">"] = Field(
        default=">",
        description="Binary greater than operator, as in 3 > 2 = true",
        title="binary-greater-op",
    )

    @classmethod
    def perform_compile(
        cls,
        left_expr: TypedSelectExpression,
        right_expr: TypedSelectExpression,
        dialect: CalcDialect,
        kind: ExpressionKind,
        timezone: str,
    ) -> TypedSelectExpression:
        left_expr, right_expr = cls._unify_types(
            left_expr, right_expr, dialect, timezone
        )
        # Wrap operands in parentheses if needed based on precedence
        left = parens_if_needed(left_expr.expression, ">", operand_type="left")
        right = parens_if_needed(right_expr.expression, ">", operand_type="right")

        gt_expr = exp.GT(this=left, expression=right)
        return TypedSelectExpression.from_sqlglot(gt_expr, DataType.BOOLEAN, kind)


class BinaryGreaterEqual(BinaryComparisonBase):
    binary: Literal[">="] = Field(
        default=">=",
        description="Binary greater than or equal operator, as in 3 >= 2 = true",
        title="binary-greater-equal-op",
    )

    @classmethod
    def perform_compile(
        cls,
        left_expr: TypedSelectExpression,
        right_expr: TypedSelectExpression,
        dialect: CalcDialect,
        kind: ExpressionKind,
        timezone: str,
    ) -> TypedSelectExpression:
        left_expr, right_expr = cls._unify_types(
            left_expr, right_expr, dialect, timezone
        )
        # Wrap operands in parentheses if needed based on precedence
        left = parens_if_needed(left_expr.expression, ">=", operand_type="left")
        right = parens_if_needed(right_expr.expression, ">=", operand_type="right")

        gte_expr = exp.GTE(this=left, expression=right)
        return TypedSelectExpression.from_sqlglot(gte_expr, DataType.BOOLEAN, kind)


class BinaryEqual(BinaryComparisonBase):
    binary: Literal["="] = Field(
        default="=",
        description="Binary equal operator, as in 3 = 3 = true",
        title="binary-equal-op",
    )

    @classmethod
    def perform_compile(
        cls,
        left_expr: TypedSelectExpression,
        right_expr: TypedSelectExpression,
        dialect: CalcDialect,
        kind: ExpressionKind,
        timezone: str,
    ) -> TypedSelectExpression:
        left_expr, right_expr = cls._unify_types(
            left_expr, right_expr, dialect, timezone
        )
        # Wrap operands in parentheses if needed based on precedence
        left = parens_if_needed(left_expr.expression, "=", operand_type="left")
        right = parens_if_needed(right_expr.expression, "=", operand_type="right")

        eq_expr = exp.EQ(this=left, expression=right)
        return TypedSelectExpression.from_sqlglot(eq_expr, DataType.BOOLEAN, kind)


class BinaryNotEqual(BinaryComparisonBase):
    binary: Literal["!="] = Field(
        default="!=",
        description="Binary not equal operator, as in 3 != 3 = false",
        title="binary-not-equal-op",
    )

    @classmethod
    def perform_compile(
        cls,
        left_expr: TypedSelectExpression,
        right_expr: TypedSelectExpression,
        dialect: CalcDialect,
        kind: ExpressionKind,
        timezone: str,
    ) -> TypedSelectExpression:
        left_expr, right_expr = cls._unify_types(
            left_expr, right_expr, dialect, timezone
        )
        # Wrap operands in parentheses if needed based on precedence
        left = parens_if_needed(left_expr.expression, "!=", operand_type="left")
        right = parens_if_needed(right_expr.expression, "!=", operand_type="right")

        neq_expr = exp.NEQ(this=left, expression=right)
        return TypedSelectExpression.from_sqlglot(neq_expr, DataType.BOOLEAN, kind)
