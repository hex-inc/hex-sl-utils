"""Build self-contained inline-VALUES queries for calc result tests."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from hex_sl_utils._vendor.sqlglot import exp, to_identifier
from hex_sl_utils.datatype import DataType
from hex_sl_utils.dialect import Dialect

if TYPE_CHECKING:
    import polars as pl


def build_values_query_for_df(
    table: pl.DataFrame,
    columns: Mapping[str, DataType],
    dialect: Dialect,
    table_alias: str = "t",
) -> exp.Select:
    """Compile one dataframe into a dialect-aware inline VALUES relation."""
    if list(columns) != table.columns:
        msg = (
            "Declared calc columns must match dataframe columns: "
            f"{list(columns)!r} != {table.columns!r}"
        )
        raise ValueError(msg)

    rows = [
        exp.Tuple(
            expressions=[
                dialect.compile_literal(
                    _normalize_literal(value, columns[column]),
                    data_type=columns[column],
                ).expression
                for column, value in zip(table.columns, row, strict=True)
            ]
        )
        for row in table.iter_rows()
    ]
    values = exp.Values(
        expressions=rows,
        alias=exp.TableAlias(
            this=to_identifier(table_alias, quoted=True),
            columns=[
                exp.to_identifier(column, quoted=True) for column in table.columns
            ],
        ),
    )
    return exp.select("*").from_(values)


def _normalize_literal(value: object, data_type: DataType) -> object:
    """Use UTC offsets for TIMESTAMPTZ literals, matching dataframe serialization."""
    if (
        data_type == DataType.TIMESTAMPTZ
        and isinstance(value, datetime)
        and value.tzinfo is not None
    ):
        return value.astimezone(timezone.utc)
    return value
