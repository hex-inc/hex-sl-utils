from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from .common import Dialect
from .entity_id import EntityId
from .model import Model
from .resource import Resource
from .view import View


class Project(BaseModel):
    """
    A Hex semantic project.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        ...,
        title="ProjectName",
        description=(
            "A display name.\n"
            "Hex can report errors using this name in certain contexts."
        ),
    )

    dialect: Dialect = Field(
        ...,
        description="The SQL dialect which queries should be rendered in.",
    )

    resources: list[Resource] = Field(
        default_factory=list,
        description="The resources defined in the project.",
    )

    @property
    def models(self) -> list[Model]:
        return [d for d in self.resources if d.type == "model"]

    @property
    def views(self) -> list[View]:
        return [v for v in self.resources if v.type == "view"]

    def get_model(self, model_id: EntityId) -> Model | None:
        return next(
            (m for m in self.models if m.id == model_id),
            None,
        )

    def get_view(self, view_id: EntityId) -> View | None:
        return next(
            (v for v in self.views if v.id == view_id),
            None,
        )
