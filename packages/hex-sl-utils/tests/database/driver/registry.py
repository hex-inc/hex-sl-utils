"""Explicit driver registry for the canonical execution matrix."""

from __future__ import annotations

from collections.abc import Iterable
from importlib import import_module

from database.driver.base import SqlDriver
from hex_sl_utils.dialect import Dialect, normalize_dialect_name

_DRIVER_CLASSES = {
    "bigquery": ("database.driver.bigquery", "BigQueryDriver"),
    "clickhouse": ("database.driver.clickhouse", "ClickHouseDriver"),
    "duckdb": ("database.driver.duckdb", "DuckDBDriver"),
    "mssql": ("database.driver.mssql", "MSSQLDriver"),
    "mysql": ("database.driver.mysql", "MySqlDriver"),
    "postgres": ("database.driver.postgres", "PostgresDriver"),
    "redshift": ("database.driver.redshift", "RedshiftDriver"),
    "snowflake": ("database.driver.snowflake", "SnowflakeDriver"),
    "spark": ("database.driver.spark", "SparkDriver"),
    "trino": ("database.driver.trino", "TrinoDriver"),
}

if set(_DRIVER_CLASSES) != set(Dialect.all_dialects):
    msg = "The SQL driver registry must cover every canonical dialect exactly once"
    raise RuntimeError(msg)


def create_driver(dialect_name: str) -> SqlDriver:
    """Construct the requested target without swallowing connection failures."""
    canonical_name = normalize_dialect_name(dialect_name)
    module_name, class_name = _DRIVER_CLASSES[canonical_name]
    driver_class = getattr(import_module(module_name), class_name)
    return driver_class()


def normalize_requested_dialects(dialect_names: Iterable[str]) -> tuple[str, ...]:
    """Validate an explicit target list while preserving its requested order."""
    normalized: list[str] = []
    for dialect_name in dialect_names:
        canonical_name = normalize_dialect_name(dialect_name)
        if canonical_name in normalized:
            msg = f"Database dialect requested more than once: {canonical_name}"
            raise ValueError(msg)
        normalized.append(canonical_name)
    return tuple(normalized)
