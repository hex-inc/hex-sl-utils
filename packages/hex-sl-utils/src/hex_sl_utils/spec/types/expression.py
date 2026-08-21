from __future__ import annotations

from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)
from pydantic.json_schema import SkipJsonSchema
from pydantic_core import PydanticCustomError
from typing_extensions import Self

from .common import DataType


class ScalarExpression(BaseModel):
    """
    Represents a selectable column expression.

    These can be physical columns, complex SQL snippets, or formulas.
    """

    model_config = ConfigDict(extra="forbid")

    # This is included here to consistently order it as the first field in
    # subclasses which affects serialization and JSON schema ordering. In this
    # base class, it is marked as 'Any' and skipped since it should not
    # actually be loaded into instances of the base class.
    id: SkipJsonSchema[Any] = Field(default=None, exclude=True)

    type: DataType = Field(
        ..., description="The abstract data type of this expression."
    )

    expr_sql: str | None = Field(
        default=None,
        description=(
            "A sql select column expression that produces a scalar for each row. "
            "This is often a column name.\n"
            "One of `expr_sql` or `expr_calc` can be provided. If neither is "
            "provided, defaults to `expr_sql` being the `id` of this dimension."
        ),
    )

    expr_calc: str | None = Field(
        default=None,
        description=(
            "A [Hex calc formula](https://learn.hex.tech/docs/explore-data/cells/calculations)"
            " which produces a scalar for each row."
        ),
    )

    @model_validator(mode="after")
    def _expr_validator(self) -> Self:
        if self.expr_sql and self.expr_calc:
            raise PydanticCustomError(
                "custom.extra_forbidden",
                "Only one of `expr_sql` or `expr_calc` can be provided",
                {"conflict_keys": ["expr_sql", "expr_calc"]},
            )
        return self


class _ScalarExpressionWithDefaultType(ScalarExpression):
    model_config = ConfigDict(
        json_schema_extra={
            "oneOf": [
                {"required": ["expr_sql"]},
                {"required": ["expr_calc"]},
            ]
        }
    )

    type: DataType = Field(default=NotImplemented)


class ScalarExpressionDefaultBoolean(_ScalarExpressionWithDefaultType):
    type: DataType = Field(default=DataType.BOOLEAN)


class ScalarExpressionDefaultNumber(_ScalarExpressionWithDefaultType):
    type: DataType = Field(default=DataType.NUMBER)
