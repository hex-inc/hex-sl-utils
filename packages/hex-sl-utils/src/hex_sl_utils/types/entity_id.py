from typing import Annotated, Any

from pydantic import AfterValidator, Field
from pydantic_core import PydanticCustomError
from typing_extensions import TypeAliasType

ID_PATTERN = r"^[a-z_][a-z0-9_]{1,127}$"
RESERVED_IDS = [
    "dataset",
    "model",
    "this",
    "self",
    "env",
]
RESERVED_ID_PREFIX = "__hex"


def exclude_reserved_ids(entity_id: str) -> str:
    if entity_id in RESERVED_IDS:
        raise PydanticCustomError(
            "custom.string_disallowed",
            "ID '{entity_id}' is a reserved term and cannot be used",
            {"entity_id": entity_id},
        )
    elif entity_id.startswith(RESERVED_ID_PREFIX):
        raise PydanticCustomError(
            "custom.string_disallowed",
            "ID '{entity_id}' cannot begin with '{RESERVED_ID_PREFIX}'",
            {"entity_id": entity_id, "RESERVED_ID_PREFIX": RESERVED_ID_PREFIX},
        )
    return entity_id


ENTITY_ID_DESCRIPTION = f"""All IDs must conform to the following rules:

- Begins with a lowercase letter or an underscore
- Only contains lowercase letters, underscores, and numbers
- Between 2 and 128 characters long (inclusive)

In addition, the following IDs are reserved by the system and cannot be used:
{", ".join(RESERVED_IDS)} or any ID beginning with '{RESERVED_ID_PREFIX}'.
"""

EntityId = TypeAliasType(
    "EntityId",
    Annotated[
        str,
        Field(
            title="EntityId",
            description=ENTITY_ID_DESCRIPTION,
            pattern=ID_PATTERN,
            min_length=2,
            max_length=128,
            json_schema_extra={
                "not": {
                    "anyOf": [
                        {"enum": list(RESERVED_IDS)},
                        {"pattern": f"^{RESERVED_ID_PREFIX}"},
                    ]
                },
            },
        ),
        AfterValidator(exclude_reserved_ids),
    ],
)


def id_to_name(entity_id: EntityId) -> str:
    words = entity_id.split("_")
    words[0] = words[0].title()
    return " ".join(words)


def name_from_id_default_factory(d: dict[str, Any]) -> str:
    return id_to_name(d.get("id", ""))
