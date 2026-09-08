from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from .aggregate_expression import AggregateExpression
from .common import DataType, Visibility
from .entity_id import EntityId, name_from_id_default_factory

if TYPE_CHECKING:
    from ._context import RecoveryContext


class Measure(AggregateExpression):
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

    id: EntityId = Field(  # pyright: ignore[reportGeneralTypeIssues]
        ...,
        description=(
            "The unique identifier for this measure.\n"
            "This identifier is used as its reference and must be unique across all "
            "measures in this model. Changing this identifier may invalidate "
            "existing references."
        ),
    )

    # redeclared to update the description to say `measure` instead of `expression`
    type: DataType = Field(
        default=DataType.NUMBER,
        description=(
            "The abstract data type of this measure.\nIf omitted, defaults to `number`."
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
        default="",
        description="The user-facing description of this measure.",
    )

    visibility: Visibility = Field(
        default=Visibility.PUBLIC,
        description="The visibility of this measure.",
    )

    semi_additive: SemiAdditive | None = Field(
        default=None,
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
