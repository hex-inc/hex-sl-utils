from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import (
    ConfigDict,
    Field,
    model_validator,
)
from pydantic_core import PydanticCustomError
from typing_extensions import Self

from .common import DataType, Visibility
from .entity_id import EntityId, name_from_id_default_factory
from .expression import ScalarExpression

if TYPE_CHECKING:
    from ._context import RecoveryContext


class Dimension(ScalarExpression):
    """
    A dimension represents a selectable column expression.

    These can be physical columns, complex SQL snippets, or formulas.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "id": "order_id",
                    "type": "string",
                    "unique": True,
                    "visibility": "internal",
                },
                {
                    "id": "is_cancelled",
                    "type": "boolean",
                    "expr_sql": "status = 'cancelled'",
                },
                {
                    "id": "price_usd",
                    "type": "number",
                    "expr_sql": "price",
                },
                {
                    "id": "price_euro",
                    "type": "number",
                    "expr_sql": "${price_usd} * 0.86",
                },
            ],
        },
    )

    id: EntityId = Field(
        ...,
        description=(
            "The unique identifier for this dimension.\n"
            "This identifier is used as its reference and must be unique across all "
            "dimensions, measures, and relations in this model. Changing this "
            "identifier may invalidate existing references."
        ),
    )

    # redeclared to update the description to say `dimension` instead of `expression`
    type: DataType = Field(..., description="The abstract data type of this dimension.")

    @model_validator(mode="after")
    def _expr_validator(self) -> Self:
        if self.expr_sql and self.expr_calc:
            raise PydanticCustomError(
                "custom.extra_forbidden",
                "Only one of `expr_sql` or `expr_calc` can be provided",
                {"conflict_keys": ["expr_sql", "expr_calc"]},
            )
        elif not self.expr_sql and not self.expr_calc:
            self.expr_sql = self.id
        return self

    unique: bool = Field(
        False,
        description=(
            "If true, this dimension is unique for all rows in this model.\n"
            "This dimension may be used in the construction of primary keys."
        ),
    )

    name: str = Field(
        default_factory=name_from_id_default_factory,
        description=(
            "The user-facing display name for this dimension.\n"
            "If omitted, defaults to the sentence-case value of `id`."
        ),
    )

    description: str = Field(
        "",
        description="The user-facing description of this dimension.",
    )

    visibility: Visibility = Field(
        Visibility.PUBLIC,
        description="The visibility of this dimension.",
    )

    @classmethod
    def validation_recovery_partial(cls, ctx: RecoveryContext) -> dict[str, Any]:
        return {
            "id": ctx.generate_programmatic_id("__unknown_dimension"),
            "expr_sql": "1",
            "expr_calc": "1",
            "type": DataType.OTHER,
            "unique": False,
            "name": "",
            "description": "",
            "visibility": Visibility.INTERNAL,
        }
