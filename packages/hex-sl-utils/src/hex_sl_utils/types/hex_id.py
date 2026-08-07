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


def exclude_reserved_ids(hex_id: str) -> str:
    if hex_id in RESERVED_IDS:
        raise PydanticCustomError(
            "custom.string_disallowed",
            "ID '{hex_id}' is a reserved term and cannot be used",
            {"hex_id": hex_id},
        )
    elif hex_id.startswith(RESERVED_ID_PREFIX):
        raise PydanticCustomError(
            "custom.string_disallowed",
            "ID '{hex_id}' cannot begin with '{RESERVED_ID_PREFIX}'",
            {"hex_id": hex_id, "RESERVED_ID_PREFIX": RESERVED_ID_PREFIX},
        )
    return hex_id


f"""
All IDs must conform to the following rules:

- Begins with a lowercase letter or an underscore
- Only contains lowercase letters, underscores, and numbers
- Between 2 and 128 characters long (inclusive)

In addition, the following IDs are reserved by the system and cannot be used:
{", ".join(RESERVED_IDS)} or any ID beginning with '{RESERVED_ID_PREFIX}'.
"""

HexID = TypeAliasType(
    "HexID",
    Annotated[
        str,
        Field(
            title="HexID",
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


def id_to_name(hex_id: HexID) -> str:
    words = hex_id.split("_")
    words[0] = words[0].title()
    return " ".join(words)


def name_from_id_default_factory(d: dict[str, Any]) -> str:
    return id_to_name(d.get("id", ""))
