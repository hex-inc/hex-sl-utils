"""Connection smoke tests for explicitly selected local database targets."""

from __future__ import annotations

import pytest

from database.driver.query import ExecutableQuery
from database.driver.registry import create_driver
from hex_sl_utils.datatype import DataType

pytestmark = [
    pytest.mark.database,
    pytest.mark.database_local,
    pytest.mark.integration,
]


def test_local_database_connection(local_database_dialect: str) -> None:
    """Execute a trivial query through each requested local driver."""
    query = ExecutableQuery(
        expression="SELECT 1 AS value",
        parameters={},
        parameter_types={},
        result_types={"value": DataType.NUMBER},
    )

    with create_driver(local_database_dialect) as driver:
        result = driver.execute(query)

    assert result.item(0, 0) == 1
