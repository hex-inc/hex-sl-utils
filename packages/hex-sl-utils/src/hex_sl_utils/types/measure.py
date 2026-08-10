from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)
from pydantic_core import PydanticCustomError
from typing_extensions import Self

from .common import DataType, Visibility
from .expression import (
    ScalarExpressionDefaultBoolean,
    ScalarExpressionDefaultNumber,
)
from .hex_id import HexID, name_from_id_default_factory

if TYPE_CHECKING:
    from ._context import RecoveryContext


class Measure(BaseModel):
    """
    A measure represents a aggregated expression.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "id": "total_sales",
                    "func": "count",
                },
                {
                    "id": "total_revenue_usd",
                    "func": "sum",
                    "of": "price_usd",
                },
                {
                    "id": "cancelled_sales_count",
                    "func": "count",
                    "filters": ["is_cancelled"],
                },
            ],
        },
    )

    id: HexID = Field(
        ...,
        description=(
            "The unique identifier for this measure.\n"
            "This identifier is used as its reference and must be unique across all "
            "measures in this model. Changing this identifier may invalidate "
            "existing references."
        ),
    )

    func: MeasureFuncName | None = Field(
        None,
        description=(
            "A standard aggregation function to use.\n"
            "One of `func`+`of`, `func_sql` or `func_calc` must be provided."
        ),
    )

    of: str | ScalarExpressionDefaultNumber | None = Field(
        None,
        description=(
            "Specifies the dimension over which the `func` aggregation is applied.\n"
            "This dimension can be specified as a referenced dimension ID, or "
            "an inline dimension. If `type` is unspecified in an inline dimension, "
            "it is assumed to be `number`."
        ),
    )

    func_sql: str | None = Field(
        None,
        description=(
            "An aggregating sql select expression that produces a scalar "
            "over a set of rows."
        ),
    )

    func_calc: str | None = Field(
        None,
        description=(
            "An aggregating "
            "[Hex calc formula](https://learn.hex.tech/docs/explore-data/cells/calculations) "
            "which produces a scalar over a set of rows."
        ),
    )

    type: DataType = Field(
        DataType.NUMBER,
        description=(
            "The abstract data type of this measure.\nIf omitted, defaults to `number`."
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

    name: str = Field(
        default_factory=name_from_id_default_factory,
        description=(
            "The user-facing display name for this measure.\n"
            "If omitted, defaults to the sentence-case value of `id`."
        ),
    )

    description: str = Field(
        "",
        description="The user-facing description of this measure.",
    )

    visibility: Visibility = Field(
        Visibility.PUBLIC,
        description="The visibility of this measure.",
    )

    semi_additive: SemiAdditive | None = Field(
        None,
        description=(
            "Semi-additive aggregation that selects specific rows before calculation.\n"
            "Filters to minimum or maximum values of the specified dimension, then "
            "aggregates only those rows.\n"
        ),
    )

    @classmethod
    def validation_recovery_partial(cls, ctx: RecoveryContext) -> dict[str, Any]:
        return {
            "id": ctx.generate_programmatic_id("__unknown_measure"),
            "func": "count",
            "of": {"expr_sql": "1"},
            "func_sql": "SUM(1)",
            "func_calc": "SUM(1)",
            "type": DataType.NUMBER,
            "filters": [],
            "name": "",
            "description": "",
            "visibility": Visibility.INTERNAL,
        }


class MeasureFuncName(str, Enum):
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


class SemiAdditive(BaseModel):
    """
    A semi-additive specification controls how measures aggregate over specific
    dimensions.

    Semi-additive measures are useful for metrics like account balances or inventory
    levels, where you want the most recent value within each group rather than
    summing all values.
    """

    model_config = ConfigDict(extra="forbid")

    over: list[SemiAdditiveOverMember] = Field(
        default_factory=list,
        description=(
            "List of dimensions that determine row selection for aggregation.\n"
            "Rows will be filtered to those with minimum or maximum values of these "
            "dimensions.\n"
            "Limited to a single dimension."
        ),
        # don't allow `groupings` without `over`
        min_length=1,
        # temporary limit of 1 for now while we verify HexSL behavior with multiple
        # dimensions
        max_length=1,
        json_schema_extra={"title": "SemiAdditiveOver"},
    )
    groupings: list[str] = Field(
        default_factory=list,
        description=(
            "List of dimension identifiers to group by when determining min/max "
            "values.\n"
            "The semi-additive filtering will be applied within each group."
        ),
        json_schema_extra={"title": "SemiAdditiveGroupings"},
    )


class SemiAdditiveOverMember(BaseModel):
    """
    A criteria for determining the rows to include in the semi-additive measure.

    Defines which dimension to use for row selection and how to select the rows.
    """

    model_config = ConfigDict(extra="forbid")

    dimension: str = Field(
        ..., description="The identifier of the dimension to use for row selection."
    )
    pick: Literal["min", "max"] = Field(
        "max",
        description=(
            "Whether to select rows with the minimum or maximum dimension value.\n"
            "If omitted, defaults to 'max'."
        ),
    )
