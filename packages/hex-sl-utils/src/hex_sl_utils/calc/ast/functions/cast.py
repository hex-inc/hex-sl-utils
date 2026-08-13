from typing import TYPE_CHECKING, Literal

from pydantic import Field

from hex_sl._vendor.sqlglot import exp
from hex_sl.calc.ast.functions.base import FuncBase
from hex_sl.datatype import DataType
from hex_sl.dialect.base import HexSLDialect
from hex_sl.expr import ExpressionContext, TypedSelectExpression
from hex_sl.utils import TypeCheckError

if TYPE_CHECKING:
    # This import seems to be needed to help mypy follow that the FuncBase
    # args property is available in child classes
    from hex_sl.calc.ast.args import Args  # noqa: F401


class FuncToText(FuncBase):
    """toText(expr) function"""

    fun: Literal["totext"] = Field(
        default="totext",
        description=("ToText function, as in toText(4) = '4'"),
        title="function-totext",
    )

    def compile(
        self,
        arg_exprs: list[TypedSelectExpression],
        dialect: HexSLDialect,
        context: ExpressionContext,
        tz: str,
    ) -> TypedSelectExpression:
        (arg,) = self._validate_n_args(arg_exprs, 1)
        # Note: Casts to strings use `.cast` instead of `.try_cast` because is should be
        # infallible and try_cast results in an error sometimes in using BigQuery
        # when cast succeeds
        if arg.data_type == DataType.STRING:
            # Already text
            return arg
        elif arg.data_type == DataType.NUMBER:
            # Convert to text, but don't include decimal points in integer values
            # (even if the datatype is float)
            min_i32 = -2147483648
            max_i32 = 2147483647

            # Build conditions: floor == ceil AND arg >= min_i32 AND arg <= max_i32
            floor_expr = TypedSelectExpression.from_sqlglot(
                exp.Floor(this=arg.expression), DataType.NUMBER, arg.kind
            )
            ceil_expr = TypedSelectExpression.from_sqlglot(
                exp.Ceil(this=arg.expression), DataType.NUMBER, arg.kind
            )

            # floor == ceil
            is_int_expr = TypedSelectExpression.from_sqlglot(
                exp.EQ(this=floor_expr.expression, expression=ceil_expr.expression),
                DataType.BOOLEAN,
                arg.kind,
            )

            # arg >= min_i32
            ge_min = TypedSelectExpression.from_sqlglot(
                exp.GTE(this=arg.expression, expression=exp.Literal.number(min_i32)),
                DataType.BOOLEAN,
                arg.kind,
            )

            # arg <= max_i32
            le_max = TypedSelectExpression.from_sqlglot(
                exp.LTE(this=arg.expression, expression=exp.Literal.number(max_i32)),
                DataType.BOOLEAN,
                arg.kind,
            )

            # Combine conditions with AND
            and_expr1 = TypedSelectExpression.from_sqlglot(
                exp.And(this=is_int_expr.expression, expression=ge_min.expression),
                DataType.BOOLEAN,
                arg.kind,
            )
            and_expr2 = TypedSelectExpression.from_sqlglot(
                exp.And(this=and_expr1.expression, expression=le_max.expression),
                DataType.BOOLEAN,
                arg.kind,
            )

            # Cast arg to int32 then to string for the true branch
            int_cast = dialect.cast_to_int(arg)
            int_to_string = dialect.cast_to_string(int_cast)

            # Cast arg directly to string for the false branch
            direct_to_string = dialect.cast_to_string(arg)

            # Use dialect's build_ifelse
            return dialect.build_ifelse(and_expr2, int_to_string, direct_to_string)
        elif arg.data_type == DataType.BOOLEAN:
            # Convert to lower case "true" or "false" strings
            true_literal = dialect.compile_literal("true")
            false_literal = dialect.compile_literal("false")
            return dialect.build_ifelse(arg, true_literal, false_literal)
        elif arg.data_type == DataType.TIMESTAMP:
            # Use dialect-specific timestamp-to-string conversion
            return dialect.cast_timestamp_to_string(arg)
        else:
            # Regular cast to string
            return dialect.cast_to_string(arg)


class FuncToNumber(FuncBase):
    """toNumber(expr) function"""

    fun: Literal["tonumber"] = Field(
        default="tonumber",
        description=("ToNumber function, as in toNumber('4') = 4"),
        title="function-tonumber",
    )

    def compile(
        self,
        arg_exprs: list[TypedSelectExpression],
        dialect: HexSLDialect,
        context: ExpressionContext,
        tz: str,
    ) -> TypedSelectExpression:
        (arg,) = self._validate_n_args(arg_exprs, 1)

        if arg.data_type == DataType.NUMBER:
            # Already number
            return arg
        elif arg.data_type == DataType.BOOLEAN:
            one_literal = dialect.compile_literal(1)
            zero_literal = dialect.compile_literal(0)
            return dialect.build_ifelse(arg, one_literal, zero_literal)
        elif arg.data_type == DataType.STRING:
            return dialect.cast_str_to_number(arg)
        else:
            # Regular cast to number with TRY_CAST
            return TypedSelectExpression.from_sqlglot(
                exp.TryCast(this=arg.expression, to=exp.DataType.build("DOUBLE")),
                DataType.NUMBER,
                arg.kind,
            )


class FuncToBoolean(FuncBase):
    """toBoolean(expr) function"""

    fun: Literal["toboolean"] = Field(
        default="toboolean",
        description=("ToBoolean function, as in toBoolean('true') = true"),
        title="function-toboolean",
    )

    @classmethod
    def _compile_to_boolean(
        cls, arg: TypedSelectExpression, dialect: HexSLDialect
    ) -> TypedSelectExpression:
        if arg.data_type == DataType.BOOLEAN:
            # Already boolean
            return arg
        elif arg.data_type == DataType.STRING:
            # Convert to boolean
            # This approach makes sure the we don't return a boolean
            # as an intermediate result from the case clause (which breaks in
            # sqlserver), but only as the result of the final expression.

            # Build lower(arg)
            lower_expr = TypedSelectExpression.from_sqlglot(
                exp.Lower(this=arg.expression), DataType.STRING, arg.kind
            )

            # Build conditions for CASE
            # lower(arg) IN ('true', '1')
            true_values = [exp.Literal.string("true"), exp.Literal.string("1")]
            in_true = TypedSelectExpression.from_sqlglot(
                exp.In(this=lower_expr.expression, expressions=true_values),
                DataType.BOOLEAN,
                arg.kind,
            )

            # lower(arg) IN ('false', '0')
            false_values = [exp.Literal.string("false"), exp.Literal.string("0")]
            in_false = TypedSelectExpression.from_sqlglot(
                exp.In(this=lower_expr.expression, expressions=false_values),
                DataType.BOOLEAN,
                arg.kind,
            )

            # Build boolean literals for CASE statement
            # Use PROJECTION context to handle dialect-specific boolean conversion
            true_literal = dialect.compile_literal(True, ExpressionContext.PROJECTION)
            false_literal = dialect.compile_literal(False, ExpressionContext.PROJECTION)
            null_literal = dialect.build_null(true_literal.data_type)

            case_expr = dialect.build_case(
                [(in_true, true_literal), (in_false, false_literal)], null_literal
            )

            # Use WHERE context to convert result to boolean
            # (handles MSSQL integer->boolean conversion)
            return dialect.wrap_expression_for_context(
                case_expr, ExpressionContext.WHERE
            )
        elif arg.data_type == DataType.NUMBER:
            # Convert to boolean (arg != 0)
            return TypedSelectExpression.from_sqlglot(
                exp.NEQ(this=arg.expression, expression=exp.Literal.number(0)),
                DataType.BOOLEAN,
                arg.kind,
            )
        else:
            # Regular cast to boolean with TRY_CAST
            return TypedSelectExpression.from_sqlglot(
                exp.TryCast(this=arg.expression, to=exp.DataType.build("BOOLEAN")),
                DataType.BOOLEAN,
                arg.kind,
            )

    def compile(
        self,
        arg_exprs: list[TypedSelectExpression],
        dialect: HexSLDialect,
        context: ExpressionContext,
        tz: str,
    ) -> TypedSelectExpression:
        (arg,) = self._validate_n_args(arg_exprs, 1)
        return self._compile_to_boolean(arg, dialect)


class FuncToDatetime(FuncBase):
    """toDatetime(expr) function"""

    fun: Literal["todatetime"] = Field(
        default="todatetime",
        description=(
            "ToDatetime function, as in "
            "toDatetime('2021-01-01 12:00:00') = t\"2021-01-01 12:00:00\""
        ),
        title="function-todatetime",
    )

    def compile(
        self,
        arg_exprs: list[TypedSelectExpression],
        dialect: HexSLDialect,
        context: ExpressionContext,
        tz: str,
    ) -> TypedSelectExpression:
        if len(arg_exprs) == 0 or len(arg_exprs) > 2:
            msg = f"Expected 1 or 2 arguments for {self.fun}, got {len(arg_exprs)}"
            raise TypeCheckError(msg)

        # Get expression to cast
        arg = arg_exprs[0]

        # Get optional timezone argument
        if len(arg_exprs) == 2:
            if isinstance(arg_exprs[1].expression, exp.Literal):
                val = arg_exprs[1].expression.to_py()
                if isinstance(val, str):
                    expr_tz = val
                else:
                    msg = (
                        "Expected timezone argument to ToDatetime to be a string, "
                        f"got {type(val)}"
                    )
                    raise TypeCheckError(msg)
            elif isinstance(
                (cast_expr := arg_exprs[1].expression), exp.Cast
            ) and isinstance(cast_expr.this, exp.Literal):
                # Some dialects cast string literals
                val = cast_expr.this.to_py()
                if isinstance(val, str):
                    expr_tz = val
                else:
                    msg = (
                        "Expected timezone argument to ToDatetime to be a string, "
                        f"got {type(val)}"
                    )
                    raise TypeCheckError(msg)
            else:
                msg = (
                    "Expected timezone argument to ToDatetime to be a string literal, "
                    f"got {type(arg_exprs[1].expression)}"
                )
                raise TypeCheckError(msg)
        else:
            expr_tz = None

        if arg.data_type == DataType.STRING:
            if expr_tz:
                timestamp_expr = dialect.cast_str_to_timestamp(
                    arg, expr_tz, force_tz=True
                )
            else:
                timestamp_expr = dialect.cast_str_to_timestamp(arg, tz)
        elif arg.data_type in (DataType.TIMESTAMP, DataType.TIMESTAMPTZ):
            # Already timestamp
            timestamp_expr = arg
        elif arg.data_type == DataType.DATE:
            if expr_tz:
                timestamp_expr = dialect.cast_date_to_timestamptz(arg, expr_tz)
            else:
                timestamp_expr = dialect.cast_date_to_timestamp(arg)
        else:
            # Regular cast to datetime with TRY_CAST
            timestamp_expr = TypedSelectExpression.from_sqlglot(
                exp.TryCast(this=arg.expression, to=exp.DataType.build("TIMESTAMP")),
                DataType.TIMESTAMP,
                arg.kind,
            )
        if expr_tz and timestamp_expr.data_type == DataType.TIMESTAMP:
            timestamp_expr = dialect.at_timezone(timestamp_expr, expr_tz)

        return timestamp_expr


class FuncToDate(FuncBase):
    """toDate(expr) function"""

    fun: Literal["todate"] = Field(
        default="todate",
        description=("ToDate function, as in toDate('2021-01-01') = d\"2021-01-01\""),
        title="function-todate",
    )

    def compile(
        self,
        arg_exprs: list[TypedSelectExpression],
        dialect: HexSLDialect,
        context: ExpressionContext,
        tz: str,
    ) -> TypedSelectExpression:
        (arg,) = self._validate_n_args(arg_exprs, 1)

        if arg.data_type == DataType.STRING:
            return dialect.cast_str_to_date(arg)
        elif arg.data_type == DataType.TIMESTAMPTZ:
            return dialect.cast_timestamptz_to_date(arg, tz)
        elif arg.data_type == DataType.TIMESTAMP:
            return dialect.cast_timestamp_to_date(arg)
        elif arg.data_type == DataType.DATE:
            # Already date
            return arg
        else:
            # Regular cast to date with TRY_CAST
            return TypedSelectExpression.from_sqlglot(
                exp.TryCast(this=arg.expression, to=exp.DataType.build("DATE")),
                DataType.DATE,
                arg.kind,
            )
