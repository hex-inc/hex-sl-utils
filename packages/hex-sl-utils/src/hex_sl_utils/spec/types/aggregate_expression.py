from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)
from pydantic.json_schema import SkipJsonSchema
from pydantic_core import PydanticCustomError
from typing_extensions import Self

from .common import DataType
from .scalar_expression import (
    ScalarExpressionDefaultBoolean,
    ScalarExpressionDefaultNumber,
)


# has to be declared before AggregateExpression so json schema generator
# can see it
class AggregateFuncName(str, Enum):
    """
    An aggregation function.
    """

    COUNT = "count"
    COUNT_DISTINCT = "count_distinct"
    SUM = "sum"
    SUM_BOOLEAN = "sum_boolean"
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    MEDIAN = "median"
    STDDEV = "stddev"
    STDDEV_POP = "stddev_pop"
    VARIANCE = "variance"
    VARIANCE_POP = "variance_pop"


class AggregateExpression(BaseModel):
    """
    Represents a selectable expression computed over a set of rows.

    These can be standard aggregations, complex SQL snippets, or formulas
    composed from other aggregate expressions.
    """

    model_config = ConfigDict(extra="forbid")

    # This is included here to consistently order it as the first field in
    # subclasses which affects serialization and JSON schema ordering. In this
    # base class, it is marked as 'Any' and skipped since it should not
    # actually be loaded into instances of the base class.
    id: SkipJsonSchema[Any] = Field(default=None, exclude=True)

    type: DataType = Field(
        default=DataType.NUMBER,
        description=("The abstract data type of this expression."),
    )

    func: AggregateFuncName | None = Field(
        default=None,
        description=(
            "A standard aggregation function to use.\n"
            "One of `func`+`of`, `func_sql` or `func_calc` must be provided."
        ),
    )

    of: str | ScalarExpressionDefaultNumber | None = Field(
        default=None,
        description=(
            "Specifies the dimension over which the `func` aggregation is applied.\n"
            "This dimension can be specified as a referenced dimension ID, or "
            "an inline dimension. If `type` is unspecified in an inline dimension, "
            "it is assumed to be `number`."
        ),
    )

    filters: list[str | ScalarExpressionDefaultBoolean] = Field(
        default_factory=list,
        description=(
            "A list of boolean dimensions which must be true for a row to be "
            "included in the measure's aggregation.\n"
            "Only supported for `func` measures.\n"
            "These dimensions can be specified as a referenced dimension ID, or "
            "an inline dimension. If `type` is unspecified in an inline dimension, "
            "it is assumed to be `boolean`."
        ),
    )

    func_sql: str | None = Field(
        default=None,
        description=(
            "An aggregating sql select expression that produces a scalar "
            "over a set of rows."
        ),
    )

    func_calc: str | None = Field(
        default=None,
        description=(
            "An aggregating "
            "[Hex calc formula](https://learn.hex.tech/docs/explore-data/cells/calculations) "
            "which produces a scalar over a set of rows."
        ),
    )

    @model_validator(mode="after")
    def _func_validator(self) -> Self:
        specified_keys = [
            key
            for key in ["func", "func_sql", "func_calc"]
            if getattr(self, key) is not None
        ]
        if len(specified_keys) == 0:
            raise PydanticCustomError(
                "custom.missing",
                "One of `func`, `func_sql`, or `func_calc` must be provided",
            )
        elif len(specified_keys) > 1:
            raise PydanticCustomError(
                "custom.extra_forbidden",
                "Only one of `func`, `func_sql`, or `func_calc` can be provided",
                {"conflict_keys": specified_keys},
            )
        if self.func:
            if not self.of and self.func != "count":
                raise PydanticCustomError(
                    "custom.missing",
                    "`of` is required when `func` is provided and is not `count`",
                )
            if self.type != DataType.NUMBER:
                raise PydanticCustomError(
                    "custom.literal_error",
                    "When using `func`, data type must be `number`",
                )
        elif self.of:
            used_key = "func_sql" if self.func_sql else "func_calc"
            raise PydanticCustomError(
                "custom.extra_forbidden",
                f"`of` is not allowed when using `{used_key}`",
                {"conflict_keys": ["of", used_key]},
            )
        if self.filters and (self.func_sql or self.func_calc):
            used_key = "func_sql" if self.func_sql else "func_calc"
            raise PydanticCustomError(
                "custom.extra_forbidden",
                f"`filters` is not supported when using `{used_key}`",
                {"conflict_keys": ["filters", used_key]},
            )
        return self
