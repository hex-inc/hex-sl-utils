from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field


class Problem(BaseModel):
    """
    A problem encountered during the import of a Hex project.
    """

    model_config = ConfigDict(title="HexProblem")

    severity: ProblemSeverity
    message: str = Field(json_schema_extra={"title": "ProblemMessage"})

    cause_paths: list[KeyPath]
    """
    The paths in the Hex project's specification that caused the problem.
    If empty, a cause cannot be determined.
    """

    impact_paths: list[KeyPath]
    """
    The paths in the Hex project's specification that are impacted by the problem.
    If empty, the impact cannot be determined.
    """

    validated_by_json_schema: bool = False
    """
    Whether the problem can be validated by the generated JSON schema for
    Hex types. These problems can be filtered out in contexts where
    JSON schema validation has already been performed.
    """

    def to_str(
        self,
        *,
        include_causes: bool = True,
        include_impacts: bool = True,
    ) -> str:
        causes = ", ".join(str(path) for path in self.cause_paths)
        impacts = ", ".join(str(path) for path in self.impact_paths)
        return "\n".join(
            s
            for s in [
                f"[{self.severity.upper()}] {self.message}",
                f"Cause: {causes}" if causes and include_causes else "",
                f"Impact: {impacts}" if impacts and include_impacts else "",
            ]
            if s
        )


KeyPath = Annotated[
    list[Union[str, int]],
    Field(title="ProblemKeyPath"),
]
"""
The key path to a problem's cause or impacted key, starting from the root of
the Hex project's specification and ending at the key that caused the
problem. Each key is a declared identifier.

If a key begins with `?` then it is a best guess at the location.
If a keypath ends with `:`, then the problem should be reported on the key
itself, not the value the key points to.

This is an empty list if it applies globally.
"""

ProblemSeverity = Annotated[
    Literal["fatal", "error", "warning"],
    Field(title="ProblemSeverity"),
]
"""
The severity of a problem.

- `fatal`: The problem causes invalidation that cannot be recovered from, or
           an unexpected internal error. The project cannot be used.

- `error`: The problem invalidates a definition which must be omitted from
           the result. The associated definition(s) have been omitted
           from the result.

- `warning`: The problem is a potential issue that probably should be addressed,
             but is not critical. The associated definitions may behave unexpectedly,
             but are included in the result.
"""
