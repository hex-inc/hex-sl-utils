from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, Union

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from .entity_id import EntityId, name_from_id_default_factory

if TYPE_CHECKING:
    from ._context import RecoveryContext


# It'd be nice to use `*` here, but `*` is a reserved symbol in YAML
# when used as a value
WILDCARD_SYMBOL = "..."
WildcardSymbolLiteral = Literal["..."]

# Used to omit an item from a wildcard group
WILDCARD_OMIT_PREFIX_SYMBOL = "~"


class View(BaseModel):
    """
    A semantic view represents a curated set of model properties and join paths.

    Views can be used to define a fit-for-purpose exposure of models and their
    properties, providing a cleaner sandbox for users and agents interacting with
    your semantic project.
    """

    model_config = ConfigDict(extra="forbid")

    id: EntityId = Field(
        ...,
        description=(
            "The unique identifier for this view.\n"
            "This identifier is used as its reference and must be unique across all "
            "views in the project. Changing this identifier may invalidate existing "
            "references."
        ),
    )

    type: Literal["view"] = Field(
        default="view",
        description=(
            "The type of this resource. `model` for data models, `view` for views."
        ),
    )

    base: str = Field(
        ...,
        description="The ID of the model that this view is based on.",
    )

    contents: list[ViewContentsGroup] = Field(
        ...,
        description="The contents of the view.",
    )

    name: str = Field(
        default_factory=name_from_id_default_factory,
        description=(
            "The user-facing display name for this view.\n"
            "If omitted, defaults to the sentence-case value of `id`."
        ),
    )

    description: str = Field(
        default="",
        description="The user-facing description of this view.",
    )

    @classmethod
    def validation_recovery_partial(cls, ctx: RecoveryContext) -> dict[str, Any]:
        return {
            "id": ctx.generate_programmatic_id("__unknown_view"),
            "name": "",
            "description": "",
            "base": "",
            "contents": [],
        }


class ViewContentsGroup(BaseModel):
    model_config = ConfigDict(extra="forbid")

    relation: str | None = Field(
        default=None,
        description=(
            "The relation path acting as a base for this content group.\n"
            "When omitted, references the base model."
        ),
    )

    name: str | None = Field(
        default=None,
        description=(
            "User-facing display name for this content group.\n"
            "If omitted, defaults to the name of the `relation` or `base`."
        ),
    )

    description: str | None = Field(
        default=None,
        description=(
            "User-facing description for this content group.\n"
            "If omitted, defaults to the description of the `relation` or `base`."
        ),
    )

    dimensions: ViewContentsDimensionItemList = Field(
        default_factory=list,
        description=(
            "The list of dimensions at this level to include.\n"
            f"The wildcard `{WILDCARD_SYMBOL}` can be used to include "
            "all dimensions at this level. "
            f"To omit an item, prefix it with `{WILDCARD_OMIT_PREFIX_SYMBOL}`."
        ),
    )

    measures: ViewContentsMeasureItemList = Field(
        default_factory=list,
        description=(
            "The list of measures at this level to include.\n"
            f"The wildcard `{WILDCARD_SYMBOL}` can be used to include "
            "all measures at this level. "
            f"To omit an item, prefix it with `{WILDCARD_OMIT_PREFIX_SYMBOL}`."
        ),
    )

    contents: list[ViewContentsGroup] = Field(
        default_factory=list,
        description="Content nested within this group.",
    )


class ViewContentDimensionItem(BaseModel):
    """
    A dimension included within a view content group.
    """

    dimension: str = Field(
        ...,
        description="The ID path to the dimension to include.",
    )

    name: str | None = Field(
        default=None,
        description="Override the user-facing display name for this dimension.",
    )

    description: str | None = Field(
        default=None,
        description="Override the user-facing description for this dimension.",
    )


ViewContentsDimensionItemList = Union[
    WildcardSymbolLiteral, list[Union[str, ViewContentDimensionItem]]
]


class ViewContentMeasureItem(BaseModel):
    """
    A measure included within a view content group.
    """

    measure: str = Field(
        ...,
        description="The ID path to the measure to include.",
    )

    name: str | None = Field(
        default=None,
        description="Override the user-facing display name for this measure.",
    )

    description: str | None = Field(
        default=None,
        description="Override the user-facing description for this measure.",
    )


ViewContentsMeasureItemList = Union[
    WildcardSymbolLiteral, list[Union[str, ViewContentMeasureItem]]
]
