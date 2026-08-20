"""Pytest selection helpers for explicit database execution targets."""

from __future__ import annotations

from collections.abc import Iterable
from typing import cast

import pytest
from database.driver.registry import normalize_requested_dialects

from hex_sl_utils.dialect import Dialect

LOCAL_DIALECTS = frozenset(
    {"clickhouse", "duckdb", "mssql", "mysql", "postgres", "spark", "trino"}
)
_EXPRESSION_RESULTS = "calc/compiler/snapshot/expressions"


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register explicit database target selection."""
    group = parser.getgroup("database")
    group.addoption(
        "--dialect",
        action="append",
        default=[],
        metavar="DIALECT",
        help="Canonical database dialect, optionally comma-separated.",
    )


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Parameterize selected database tests without affecting SQL snapshots."""
    if "local_database_dialect" in metafunc.fixturenames:
        dialects = [
            dialect
            for dialect in _requested_dialects(metafunc.config)
            if dialect in LOCAL_DIALECTS
        ]
        metafunc.parametrize("local_database_dialect", dialects)
        return

    parametrized = any(
        "dialect_name" in marker.args[0]
        for marker in metafunc.definition.iter_markers("parametrize")
    )
    if (
        "dialect_name" in metafunc.fixturenames
        and _EXPRESSION_RESULTS in metafunc.definition.path.as_posix()
        and metafunc.function.__name__.endswith("_validate")
        and not parametrized
    ):
        metafunc.parametrize(
            "dialect_name",
            [
                pytest.param(
                    dialect,
                    id=dialect,
                    marks=[
                        pytest.mark.database,
                        pytest.mark.database_local
                        if dialect in LOCAL_DIALECTS
                        else pytest.mark.database_cloud,
                    ],
                )
                for dialect in _requested_dialects(metafunc.config)
            ],
        )


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Deselect fixed-dialect dataframe snapshots outside ``--dialect``."""
    requested_dialects = set(_requested_dialects(config))
    deselected: list[pytest.Item] = []
    selected: list[pytest.Item] = []
    for item in items:
        is_result_snapshot = (
            _EXPRESSION_RESULTS in item.path.as_posix()
            and item.name.endswith("_result")
        )
        snapshot_test = getattr(getattr(item, "module", None), "SnapshotTest", None)
        if (
            is_result_snapshot
            and snapshot_test is not None
            and snapshot_test.result_dialect not in requested_dialects
        ):
            deselected.append(item)
        else:
            selected.append(item)

    if deselected:
        config.hook.pytest_deselected(items=deselected)
        items[:] = selected


def _requested_dialects(config: pytest.Config) -> tuple[str, ...]:
    values = cast(list[str], config.getoption("dialect") or [])
    if not values:
        return tuple(Dialect.all_dialects)
    return normalize_requested_dialects(_split_dialect_values(values))


def _split_dialect_values(values: Iterable[str]) -> Iterable[str]:
    for value in values:
        yield from (dialect.strip() for dialect in value.split(",") if dialect.strip())
