"""Focused unit tests for the test-only SQL driver boundary."""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

pl = pytest.importorskip("polars")
from polars import DataFrame

from database.driver import registry
from database.driver.base import SqlDriver
from database.driver.connection import (
    ConnectionVarsNotSetError,
    get_env_port,
    get_env_var,
    get_local_port,
)
from database.driver.query import ExecutableQuery, RenderedQuery, render_query
from database.driver.registry import create_driver, normalize_requested_dialects
from hex_sl_utils.datatype import DataType
from hex_sl_utils.dialect import Dialect
from hex_sl_utils.placeholder import PlaceholderStyle


def _query() -> ExecutableQuery:
    return ExecutableQuery(
        expression="SELECT {{foo}}, {{bar}} + {{foo}}",
        parameters={"foo": 2, "bar": 3, "unused": 5},
        parameter_types={
            "foo": DataType.NUMBER,
            "bar": DataType.NUMBER,
            "unused": DataType.NUMBER,
        },
        result_types={"value": DataType.NUMBER},
    )


def test_render_query_binds_named_parameters() -> None:
    rendered = render_query(
        _query(), Dialect.from_name("postgres"), PlaceholderStyle.COLON_NAMED
    )

    assert rendered.sql == "SELECT :foo, :bar + :foo"
    assert rendered.parameters == {"foo": 2, "bar": 3}


def test_render_query_binds_positional_parameters_in_occurrence_order() -> None:
    rendered = render_query(
        _query(), Dialect.from_name("redshift"), PlaceholderStyle.FORMAT
    )

    assert rendered.sql == "SELECT %s1, %s2 + %s3"
    assert rendered.parameters == [2, 3, 2]


def test_render_query_requires_each_used_parameter() -> None:
    query = ExecutableQuery(
        expression="SELECT {{required}}",
        parameters={},
        parameter_types={"required": DataType.STRING},
        result_types={},
    )

    with pytest.raises(ValueError, match="required"):
        render_query(query, Dialect.from_name("postgres"), PlaceholderStyle.COLON_NAMED)


def test_explicit_dialect_selection_normalizes_aliases() -> None:
    assert normalize_requested_dialects(["DuckDB", "athena"]) == ("duckdb", "trino")


def test_explicit_dialect_selection_rejects_duplicates() -> None:
    with pytest.raises(ValueError, match="more than once"):
        normalize_requested_dialects(["duckdb", "motherduck"])


def test_driver_registry_constructs_only_the_requested_target(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        registry,
        "import_module",
        lambda module_name: SimpleNamespace(DuckDBDriver=_ClosingDriver),
    )

    assert isinstance(create_driver("duckdb"), _ClosingDriver)


def test_missing_connection_setting_names_the_driver(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("TEST_DATABASE_URL", raising=False)

    with pytest.raises(ConnectionVarsNotSetError, match="TEST_DATABASE_URL"):
        get_env_var("TEST_DATABASE_URL", "test")


def test_local_port_uses_the_configured_dialect_port(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HEX_SL_UTILS_DATABASE_POSTGRES_PORT", "15437")

    assert get_local_port("postgres", 5437) == 15437


def test_local_port_rejects_an_invalid_port(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HEX_SL_UTILS_DATABASE_POSTGRES_PORT", "invalid")

    with pytest.raises(ValueError, match="HEX_SL_UTILS_DATABASE_POSTGRES_PORT"):
        get_local_port("postgres", 5437)


@pytest.mark.database
@pytest.mark.database_cloud
def test_bigquery_parameter_types_match_the_source_driver() -> None:
    pytest.importorskip("google.cloud.bigquery")
    from database.driver.bigquery import _bigquery_type

    assert _bigquery_type(DataType.NUMBER) == "NUMERIC"
    assert _bigquery_type(DataType.TIMESTAMP) == "TIMESTAMP"
    assert _bigquery_type(DataType.TIMESTAMPTZ) == "TIMESTAMP"


@pytest.mark.database
@pytest.mark.database_local
def test_duckdb_driver_executes_a_rendered_query() -> None:
    pytest.importorskip("duckdb")
    from database.driver.duckdb import DuckDBDriver

    query = ExecutableQuery(
        expression="SELECT {{value}} AS value",
        parameters={"value": 42},
        parameter_types={"value": DataType.NUMBER},
        result_types={"value": DataType.NUMBER},
    )

    with DuckDBDriver() as driver:
        assert driver.execute(query).to_dicts() == [{"value": 42}]


def test_driver_normalizes_timestamptz_results() -> None:
    result = pl.DataFrame({"timestamp": [datetime(2024, 1, 1, tzinfo=timezone.utc)]})

    normalized = _ClosingDriver().normalize_result(
        result,
        {"timestamp": DataType.TIMESTAMPTZ},
        "America/New_York",
    )

    data_type = normalized.schema["timestamp"]
    assert isinstance(data_type, pl.Datetime)
    assert data_type.time_zone == "America/New_York"  # type: ignore[reportAttributeAccessIssue]


class _ClosingDriver(SqlDriver):
    dialect_name = "duckdb"
    placeholder_style = PlaceholderStyle.DOLLAR_NAMED

    def __init__(self) -> None:
        self.closed = False

    def execute_rendered(self, query: RenderedQuery) -> DataFrame:
        return pl.DataFrame({"value": [1]})

    def close(self) -> None:
        self.closed = True


def test_driver_context_manager_closes_resources() -> None:
    driver = _ClosingDriver()

    with driver:
        assert not driver.closed

    assert driver.closed


def test_required_port_is_converted_to_an_integer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TEST_REDSHIFT_PORT", "5439")

    assert get_env_port("TEST_REDSHIFT_PORT", "redshift") == 5439
