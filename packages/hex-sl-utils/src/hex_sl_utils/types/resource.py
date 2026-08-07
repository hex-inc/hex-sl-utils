from __future__ import annotations

from typing import Annotated, Any, cast

from pydantic import Discriminator, Tag

from .model import Model
from .view import View

DEFAULT_RESOURCE_TYPE = "model"


def discriminate_types(v: Any) -> str:
    if isinstance(v, dict):
        return cast(str, v.get("type", DEFAULT_RESOURCE_TYPE))
    return cast(str, getattr(v, "type", DEFAULT_RESOURCE_TYPE))


Resource = Annotated[
    Annotated[Model, Tag("model")] | Annotated[View, Tag("view")],
    Discriminator(discriminate_types),
]
