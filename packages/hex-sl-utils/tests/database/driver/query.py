"""Render executable test queries with a driver's native parameter style."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Union

from hex_sl_utils._vendor.sqlglot import exp, parse_one
from hex_sl_utils.datatype import DataType
from hex_sl_utils.dialect import Dialect
from hex_sl_utils.placeholder import PlaceholderStyle, set_placeholder_style

ParameterValues = Union[dict[str, Any], list[Any]]


@dataclass(frozen=True)
class ExecutableQuery:
    """A complete test query before rendering driver placeholders."""

    expression: exp.Expression | str
    parameters: Mapping[str, Any]
    parameter_types: Mapping[str, DataType]
    result_types: Mapping[str, DataType]


@dataclass(frozen=True)
class RenderedQuery:
    """A complete query ready for a driver's native execution method."""

    sql: str
    parameters: ParameterValues
    result_types: Mapping[str, DataType]
    parameter_types: Mapping[str, DataType]


_POSITIONAL_STYLES = frozenset(
    {
        PlaceholderStyle.QMARK,
        PlaceholderStyle.FORMAT,
        PlaceholderStyle.NUMERIC,
        PlaceholderStyle.ASYNCPG,
    }
)


def render_query(
    query: ExecutableQuery,
    dialect: Dialect,
    placeholder_style: PlaceholderStyle,
) -> RenderedQuery:
    """Render placeholders and retain only parameters used by the query."""
    expression = _as_expression(query.expression, dialect)
    parameter_types = dict(query.parameter_types)

    with set_placeholder_style(placeholder_style, parameter_types) as config:
        sql = expression.sql(dialect=dialect.sqlglot_dialect())

    if placeholder_style in _POSITIONAL_STYLES:
        parameters: ParameterValues = [
            _required_value(query, name) for name in config.order
        ]
    else:
        parameters = {
            name: _required_value(query, name) for name in config.used_parameters
        }

    return RenderedQuery(sql, parameters, query.result_types, config.used_parameters)


def _as_expression(
    expression: exp.Expression | str, dialect: Dialect
) -> exp.Expression:
    if isinstance(expression, exp.Expression):
        return expression.copy()
    return parse_one(expression, dialect=dialect.sqlglot_dialect())


def _required_value(query: ExecutableQuery, name: str) -> Any:
    try:
        return query.parameters[name]
    except KeyError as error:
        msg = f"Missing value for query parameter {name}"
        raise ValueError(msg) from error
