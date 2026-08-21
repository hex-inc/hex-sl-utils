from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, Field

from .common import Visibility
from .entity_id import EntityId

if TYPE_CHECKING:
    from ._context import RecoveryContext


class Relation(BaseModel):
    """
    A relation defines a link between two models, aka a "join".

    The properties of a relation can be referenced with dot-syntax within a
    bracket reference, such as `${relation_id.dimension_id}`.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "id": "message_contents",
                    "type": "one_to_one",
                    "join_sql": "${id} = ${message_contents.message_id}",
                },
                {
                    "id": "sender",
                    "target": "users",
                    "type": "many_to_one",
                    "join_sql": "${sender_id} = ${sender.id}",
                },
                {
                    "id": "receiver",
                    "target": "users",
                    "type": "many_to_one",
                    "join_sql": "${receiver_id} = ${receiver.id}",
                },
            ]
        },
    )

    id: EntityId = Field(
        ...,
        description=(
            "The unique identifier for this relation."
            "\n"
            "Typically, this should be the id of the model being joined to."
            "\n"
            "Relations with the same id will be considered symmetric "
            "with one another."
            "\n"
            "Relation ids must be unique across all dimensions, measures, and "
            "relations in this model. Changing this identifier may invalidate "
            "existing references."
        ),
    )

    target: EntityId = Field(
        default_factory=lambda d: d.get("id", ""),
        description=(
            "The identifier of the target model for this relation.\n"
            "If omitted, defaults to the value of `id`."
        ),
    )

    type: RelationType = Field(
        ...,
        description=(
            "The cardinality of the join, from the base model to the target."
            "\n"
            "This is declared to ensure Hex can properly invoke fan-out prevention."
        ),
    )

    join_sql: str = Field(
        ...,
        description=(
            "The SQL condition to join the base model to a target.\n"
            "Within this snippet, all dimensions and relations (including this one) "
            "are in scope for `${ }` interpolation."
        ),
    )

    visibility: Visibility = Field(
        default=Visibility.PUBLIC,
        description="The visibility of this relation.",
    )

    @classmethod
    def validation_recovery_partial(cls, ctx: RecoveryContext) -> dict[str, Any]:
        return {
            "id": ctx.generate_programmatic_id("__unknown_relation"),
            "join_sql": "1 = 1",
            "type": RelationType.ONE_TO_ONE,
            "visibility": Visibility.INTERNAL,
        }


class RelationType(str, Enum):
    """
    The cardinality of the join, from the base model to the target model.
    """

    MANY_TO_ONE = "many_to_one"
    ONE_TO_ONE = "one_to_one"
    ONE_TO_MANY = "one_to_many"
