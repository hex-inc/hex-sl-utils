from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import date, datetime
from typing import Any, Literal, Protocol

from typing_extensions import TypeAlias

from hex_sl_utils._vendor.sqlglot import exp
from hex_sl_utils.types import DataType

from .compiled import ExpressionContext, TypedSelectExpression

TruncUnit: TypeAlias = Literal[
    "year",
    "quarter",
    "month",
    "week",
    "weekmonday",
    "day",
    "hour",
    "minute",
    "second",
    "millisecond",
]
CalcSchema: TypeAlias = Mapping[str, DataType]


class CalcDialect(Protocol):
    """Dialect services required by the calc-to-SQL compiler.

    Hex-SL's dialect can implement or adapt this protocol during the later
    repository replacement. The calc package otherwise has no dependency on
    Hex-SL's project, schema, or query modules.
    """

    at_timezone: Callable[..., Any]
    build_case: Callable[..., Any]
    build_coalesce: Callable[..., Any]
    build_division: Callable[..., Any]
    build_ifelse: Callable[..., Any]
    build_isinf: Callable[..., Any]
    build_isnan: Callable[..., Any]
    build_isnull: Callable[..., Any]
    build_median: Callable[..., Any]
    build_null: Callable[..., Any]
    build_percentile_approx: Callable[..., Any]
    build_percentile_exact: Callable[..., Any]
    build_round: Callable[..., Any]
    cast_date_to_timestamp: Callable[..., Any]
    cast_date_to_timestamptz: Callable[..., Any]
    cast_str_to_date: Callable[..., Any]
    cast_str_to_number: Callable[..., Any]
    cast_str_to_timestamp: Callable[..., Any]
    cast_timestamp_to_date: Callable[..., Any]
    cast_timestamp_to_string: Callable[..., Any]
    cast_timestamptz_to_date: Callable[..., Any]
    cast_to_float: Callable[..., Any]
    cast_to_int: Callable[..., Any]
    cast_to_string: Callable[..., Any]
    clamp_left_right_to_str_length: Callable[..., Any]
    concat: Callable[..., Any]
    contains: Callable[..., Any]
    date_diff: Callable[..., Any]
    date_part: Callable[..., Any]
    datetime_to_epoch_ms: Callable[..., Any]
    datetime_trunc: Callable[..., Any]
    day_of_week_part: Callable[..., Any]
    endswith: Callable[..., Any]
    epoch_ms_to_timestamp: Callable[..., Any]
    mod_supports_floats: Callable[..., Any]
    now: Callable[..., Any]
    splitpart: Callable[..., Any]
    startswith: Callable[..., Any]
    str_length: Callable[..., Any]
    supports_cot_function: Callable[..., Any]
    supports_median: Callable[..., Any]
    supports_non_finite_floats: Callable[..., Any]
    supports_percentile_approx: Callable[..., Any]
    supports_percentile_exact: Callable[..., Any]
    time_part: Callable[..., Any]
    today: Callable[..., Any]
    truncates_on_integer_division: Callable[..., Any]
    use_empty_over_for_count_star_window_function: Callable[..., Any]

    def name(self) -> str: ...

    def sqlglot_dialect(self) -> str: ...

    def compile_literal(
        self, value: float | str | bool | date | datetime | None
    ) -> TypedSelectExpression: ...

    def resolve_hexsl_calc_placeholders(
        self, expression: exp.Expression, **kwargs: Any
    ) -> exp.Expression: ...

    def wrap_expression_for_context(
        self, expression: TypedSelectExpression, context: ExpressionContext
    ) -> TypedSelectExpression: ...

    def func(self, name: str, *args: Any) -> exp.Func: ...
