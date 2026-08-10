from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)
from pydantic_core import PydanticCustomError
from typing_extensions import Self

from ._utils import clean_doc_comment
from .common import Visibility
from .dimension import Dimension
from .entity_id import EntityId, name_from_id_default_factory
from .measure import Measure
from .relation import Relation

if TYPE_CHECKING:
    from ._context import RecoveryContext


class Model(BaseModel):
    """
    A semantic model represents a rectangle of data and its capabilities.
    """

    model_config = ConfigDict(extra="forbid")

    id: EntityId = Field(
        ...,
        description=(
            "The unique identifier for this model.\n"
            "This identifier is used as its reference and must be unique across all "
            "models in the project. Changing this identifier may invalidate existing "
            "references."
        ),
    )

    type: Literal["model"] = Field(
        "model",
        description=(
            "The type of this resource. `model` for data models, `view` for views."
        ),
    )

    base_sql_table: str | None = Field(
        None,
        description=(
            "A table or view in the data connection to use as the base for this model.\n"
            "One of `base_sql_query` or `base_sql_table` must be provided."
        ),
    )
    base_sql_query: str | None = Field(
        None,
        description=(
            "A SQL statement that produces a table to use as the base of this model.\n"
            "One of `base_sql_query` or `base_sql_table` must be provided."
        ),
    )

    @model_validator(mode="after")
    def _base_validator(self) -> Self:
        if not self.base_sql_query and not self.base_sql_table:
            raise PydanticCustomError(
                "custom.missing",
                "Either `base_sql_query` or `base_sql_table` must be provided",
            )
        if self.base_sql_query and self.base_sql_table:
            raise PydanticCustomError(
                "custom.extra_forbidden",
                "Only one of `base_sql_query` or `base_sql_table` can be provided",
                {"conflict_keys": ["base_sql_query", "base_sql_table"]},
            )
        return self

    dimensions: list[Dimension] = Field(
        default_factory=list,
        description=clean_doc_comment(Dimension.__doc__),
    )

    measures: list[Measure] = Field(
        default_factory=list,
        description=clean_doc_comment(Measure.__doc__),
    )

    relations: list[Relation] = Field(
        default_factory=list,
        description=clean_doc_comment(Relation.__doc__),
    )

    name: str = Field(
        default_factory=name_from_id_default_factory,
        description=(
            "The user-facing display name for this model.\n"
            "If omitted, defaults to the sentence-case value of `id`."
        ),
    )

    description: str = Field(
        "",
        description="The user-facing description of this model.",
    )

    visibility: Visibility = Field(
        Visibility.PUBLIC,
        description="The visibility of this model.",
    )

    @classmethod
    def validation_recovery_partial(cls, ctx: RecoveryContext) -> dict[str, Any]:
        return {
            "id": ctx.generate_programmatic_id("__unknown_model"),
            "base_sql_query": "SELECT * FROM table",
            "base_sql_table": "table",
            "dimensions": [],
            "measures": [],
            "relations": [],
            "name": "",
            "description": "",
            "visibility": Visibility.INTERNAL,
        }
