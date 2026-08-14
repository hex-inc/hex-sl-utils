from __future__ import annotations

from typing import Annotated, Any, Union, cast

from pydantic import Discriminator, Tag, TypeAdapter

from .model import Model
from .view import View

DEFAULT_RESOURCE_TYPE = "model"


def discriminate_types(v: Any) -> str:
    if isinstance(v, dict):
        return cast(str, v.get("type", DEFAULT_RESOURCE_TYPE))
    return cast(str, getattr(v, "type", DEFAULT_RESOURCE_TYPE))


Resource = Annotated[
    Union[Annotated[Model, Tag("model")], Annotated[View, Tag("view")]],
    Discriminator(discriminate_types),
]

_RESOURCE_ADAPTER = TypeAdapter(Resource)


def parse_resource(data: dict[str, Any]) -> Resource:
    """Parse one resource mapping without validation recovery."""
    return _RESOURCE_ADAPTER.validate_python(data)
