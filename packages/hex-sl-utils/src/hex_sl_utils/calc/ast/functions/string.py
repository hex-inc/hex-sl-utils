from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import Field

from hex_sl._vendor.sqlglot import exp
from hex_sl.calc.ast.functions.base import FuncBase
from hex_sl.datatype import DataType
from hex_sl.expr import ExpressionContext, ExpressionKind, TypedSelectExpression

if TYPE_CHECKING:
    # This import seems to be needed to help mypy follow that the BinaryBase
    # lhs/rhs CalcExpr properties are available in child classes
    from hex_sl.calc.ast.args import Args  # noqa: F401
    from hex_sl.dialect.base import HexSLDialect
    from hex_sl.expr import TypedSelectExpression


class FuncConcat(FuncBase):
    fun: Literal["concat"] = Field(
        default="concat",
        description=(
            "Concat function, as in concat('hello', ' ', 'world') = 'hello world'"
        ),
        title="function-concat",
    )

    def compile(
        self,
        arg_exprs: list[TypedSelectExpression],
        dialect: HexSLDialect,
        context: ExpressionContext,
        tz: str,
    ) -> TypedSelectExpression:
        self._validate_variadic_with_type(arg_exprs, DataType.STRING, allow_empty=True)

        # Use dialect's concat method directly (follows superclass pattern)
        return dialect.concat(*arg_exprs)


class FuncLeftRightBase(FuncBase):
    def compile(
        self,
        arg_exprs: list[TypedSelectExpression],
        dialect: HexSLDialect,
        context: ExpressionContext,
        tz: str,
    ) -> TypedSelectExpression:
        from hex_sl.utils import TypeCheckError

        arg0, arg1 = self._validate_n_args(arg_exprs, 2)

        if arg0.data_type != DataType.STRING:
            msg = (
                f"{self.fun} takes a string as the first argument, got {arg0.data_type}"
            )
            raise TypeCheckError(msg, arg0.data_type)

        if arg1.data_type != DataType.NUMBER:
            msg = (
                f"{self.fun} takes an number as the second argument, "
                f"got {arg1.data_type}"
            )
            raise TypeCheckError(msg, arg1.data_type)

        kind = ExpressionKind._validate_infer_kind([arg0.kind, arg1.kind])

        # Cast arg1 to integer
        length_expr: exp.Expression = exp.Cast(
            this=arg1.expression, to=exp.DataType.build("INT")
        )

        if dialect.clamp_left_right_to_str_length():
            # Clamp length between 0 and string length
            zero_literal = dialect.compile_literal(0)
            str_length = exp.Length(this=arg0.expression)

            # Build GREATEST(0, LEAST(length, LENGTH(string)))
            inner_least = exp.Least(this=length_expr, expressions=[str_length])
            length_expr = exp.Greatest(
                this=zero_literal.expression, expressions=[inner_least]
            )

        # Build LEFT or RIGHT function
        result_expr: exp.Expression
        if self.fun == "left":
            result_expr = exp.Left(this=arg0.expression, expression=length_expr)
        else:  # right
            result_expr = exp.Right(this=arg0.expression, expression=length_expr)

        return TypedSelectExpression.from_sqlglot(result_expr, DataType.STRING, kind)


class FuncLeft(FuncLeftRightBase):
    fun: Literal["left"] = Field(
        default="left",
        description=(
            "Take the leftmost n characters of a string, as in left('hello', 3) = 'hel'"
        ),
        title="function-left",
    )


class FuncRight(FuncLeftRightBase):
    fun: Literal["right"] = Field(
        default="right",
        description=(
            "Take the rightmost n characters of a string, "
            "as in right('hello', 3) = 'llo'"
        ),
        title="function-right",
    )


class FuncSubstitute(FuncBase):
    fun: Literal["substitute"] = Field(
        default="substitute",
        description=(
            "Replace all occurrences of a substring with another substring, "
            "as in replace('hello', 'l', 'r') = 'herr'"
        ),
        title="function-substitute",
    )

    def compile(
        self,
        arg_exprs: list[TypedSelectExpression],
        dialect: HexSLDialect,
        context: ExpressionContext,
        tz: str,
    ) -> TypedSelectExpression:
        self._validate_exact_signature(
            arg_exprs, [DataType.STRING, DataType.STRING, DataType.STRING]
        )

        string, pattern, replacement = arg_exprs

        kind = ExpressionKind._validate_infer_kind(
            [string.kind, pattern.kind, replacement.kind]
        )

        # Use dialect.func for REPLACE
        replace_expr = dialect.func(
            "REPLACE", string.expression, pattern.expression, replacement.expression
        )

        return TypedSelectExpression.from_sqlglot(replace_expr, DataType.STRING, kind)


class FuncUpper(FuncBase):
    fun: Literal["upper"] = Field(
        default="upper",
        description=("Convert a string to uppercase, as in upper('hello') = 'HELLO'"),
        title="function-upper",
    )

    def compile(
        self,
        arg_exprs: list[TypedSelectExpression],
        dialect: HexSLDialect,
        context: ExpressionContext,
        tz: str,
    ) -> TypedSelectExpression:
        arg = self._validate_single_arg(arg_exprs, DataType.STRING)

        upper_expr = exp.Upper(this=arg.expression)

        return TypedSelectExpression.from_sqlglot(upper_expr, DataType.STRING, arg.kind)


class FuncLower(FuncBase):
    fun: Literal["lower"] = Field(
        default="lower",
        description=("Convert a string to lowercase, as in lower('HELLO') = 'hello'"),
        title="function-lower",
    )

    def compile(
        self,
        arg_exprs: list[TypedSelectExpression],
        dialect: HexSLDialect,
        context: ExpressionContext,
        tz: str,
    ) -> TypedSelectExpression:
        arg = self._validate_single_arg(arg_exprs, DataType.STRING)

        lower_expr = exp.Lower(this=arg.expression)

        return TypedSelectExpression.from_sqlglot(lower_expr, DataType.STRING, arg.kind)


class FuncContains(FuncBase):
    fun: Literal["contains"] = Field(
        default="contains",
        description=(
            "Check if a string contains a substring, "
            "as in contains('hello', 'ell') = true"
        ),
        title="function-contains",
    )

    def compile(
        self,
        arg_exprs: list[TypedSelectExpression],
        dialect: HexSLDialect,
        context: ExpressionContext,
        tz: str,
    ) -> TypedSelectExpression:
        string, substring = self._validate_exact_signature(
            arg_exprs, [DataType.STRING, DataType.STRING]
        )

        return dialect.contains(string, substring)


class FuncLength(FuncBase):
    fun: Literal["length"] = Field(
        default="length",
        description=("Get the length of a string, as in length('hello') = 5"),
        title="function-length",
    )

    def compile(
        self,
        arg_exprs: list[TypedSelectExpression],
        dialect: HexSLDialect,
        context: ExpressionContext,
        tz: str,
    ) -> TypedSelectExpression:
        (arg,) = self._validate_exact_signature(arg_exprs, [DataType.STRING])

        return dialect.str_length(arg)


class FuncStartsWith(FuncBase):
    fun: Literal["startswith"] = Field(
        default="startswith",
        description=(
            "Check if a string starts with a substring, "
            "as in startswith('hello', 'hel') = true"
        ),
        title="function-startswith",
    )

    def compile(
        self,
        arg_exprs: list[TypedSelectExpression],
        dialect: HexSLDialect,
        context: ExpressionContext,
        tz: str,
    ) -> TypedSelectExpression:
        string, prefix = self._validate_exact_signature(
            arg_exprs, [DataType.STRING, DataType.STRING]
        )
        return dialect.startswith(string, prefix)


class FuncEndsWith(FuncBase):
    fun: Literal["endswith"] = Field(
        default="endswith",
        description=(
            "Check if a string ends with a substring, "
            "as in endswith('hello', 'lo') = true"
        ),
        title="function-endswith",
    )

    def compile(
        self,
        arg_exprs: list[TypedSelectExpression],
        dialect: HexSLDialect,
        context: ExpressionContext,
        tz: str,
    ) -> TypedSelectExpression:
        string, suffix = self._validate_exact_signature(
            arg_exprs, [DataType.STRING, DataType.STRING]
        )

        return dialect.endswith(string, suffix)


class FuncSplitPart(FuncBase):
    fun: Literal["splitpart"] = Field(
        default="splitpart",
        description=(
            "Splits a given string at a specified character "
            + "and returns the requested part (1-indexed)."
        ),
        title="function-splitpart",
    )

    def compile(
        self,
        arg_exprs: list[TypedSelectExpression],
        dialect: HexSLDialect,
        context: ExpressionContext,
        tz: str,
    ) -> TypedSelectExpression:
        string, delimiter, part_number = self._validate_exact_signature(
            arg_exprs, [DataType.STRING, DataType.STRING, DataType.NUMBER]
        )
        return dialect.splitpart(
            string=string,
            delimiter=delimiter,
            part_number=part_number,
        )
