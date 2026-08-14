from enum import Enum
from typing import Literal

from pydantic import RootModel

DialectName = Literal[
    "athena",
    "alloydb",
    "bigquery",
    "clickhouse",
    "databricks",
    "duckdb",
    "motherduck",
    "mssql",
    "tsql",
    "mysql",
    "prestodb",
    "postgres",
    "redshift",
    "snowflake",
    "trino",
    "spark",
    "starburst",
]


class Dialect(RootModel[DialectName]):
    model_config = {
        "json_schema_extra": {
            "title": "Dialect",
            "description": (
                "The SQL dialect to use when generating SQL from the project, and "
                "the dialect that is used for SQL fragments in the model specification."
            ),
        }
    }


class DataType(str, Enum):
    """
    An abstract data type.

    - `number` includes int, bigint, float, decimal, double, real, etc.
    - `string` includes char, varchar, text, etc.
    - `timestamp_tz` timezone-aware
    - `timestamp_naive` without timezone
    - `date` the calendar date portion of a timestamp; always without a timezone
    - `boolean`
    - `null`
    - `other`
    """

    NUMBER = "number"
    STRING = "string"
    TIMESTAMP_TZ = "timestamp_tz"
    TIMESTAMP_NAIVE = "timestamp_naive"
    DATE = "date"
    BOOLEAN = "boolean"
    NULL = "null"
    OTHER = "other"


class Visibility(str, Enum):
    """
    The visibility determines the scope the associated declaration.
    Either `public`, `internal`, or `private`.

    `visibility` is not to be relied on as a security control and is only used
    to visually hide content in the UI. For the strongest security guarantees,
    configure OAuth or role-based access within your database.
    """

    PUBLIC = "public"
    PRIVATE = "private"
    INTERNAL = "internal"
