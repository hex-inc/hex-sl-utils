from __future__ import annotations

from typing import Literal

from pydantic import BaseModel
from pydantic.fields import Field

from .hex_id import HexID


class SourceFile(BaseModel):
    filepath: str = Field(
        description="The file path, relative to the root of the project.",
    )

    contents_text: str = Field(
        description=(
            "The string contents of the file, including all comments and whitespace."
        ),
    )

    resources: list[SourceFileResource] = Field(
        default_factory=list,
        description=(
            "List of resources defined within the file, in order matching their "
            "declaration in the file."
        ),
    )


class SourceFileResource(BaseModel):
    """
    A single resource defined within a source file.
    """

    resource_type: Literal["model", "view", "unknown"] = Field(
        "unknown",
        description=(
            'The type of the resource, or "unknown" if the type could not be '
            "determined."
        ),
    )

    resource_id: HexID | None = Field(
        None,
        description=(
            "The identifier of the resource, or None if the declaration contains no id."
        ),
    )
