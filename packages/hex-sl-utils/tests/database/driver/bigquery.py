"""Credentialed BigQuery execution driver."""

from __future__ import annotations

import json
from typing import cast

import polars as pl
from google.cloud import bigquery  # type: ignore[reportAttributeAccessIssue]
from google.oauth2 import service_account  # type: ignore[reportMissingImports]

from database.driver.base import SqlDriver
from database.driver.connection import get_env_var
from database.driver.query import RenderedQuery
from hex_sl_utils.datatype import DataType
from hex_sl_utils.placeholder import PlaceholderStyle


class BigQueryDriver(SqlDriver):
    dialect_name = "bigquery"
    placeholder_style = PlaceholderStyle.AT_NAMED

    def __init__(self) -> None:
        driver_name = "bigquery"
        project_id = get_env_var("TEST_BIG_QUERY_PROJECT_ID", driver_name)
        account = get_env_var("TEST_BIG_QUERY_SERVICE_ACCOUNT", driver_name)
        service_account_info = json.loads(
            # Replace \n with \\n to avoid breaking the JSON format
            account.replace("\n", r"\n")
        )
        credentials = service_account.Credentials.from_service_account_info(
            service_account_info
        )
        self._client = bigquery.Client(
            project=project_id,
            credentials=credentials,
        )

    def execute_rendered(self, query: RenderedQuery) -> pl.DataFrame:
        """Run one rendered BigQuery query using typed named parameters."""
        if not isinstance(query.parameters, dict):
            msg = "BigQuery requires named parameters"
            raise TypeError(msg)
        bq_parameters = [
            bigquery.ScalarQueryParameter(
                name,
                _bigquery_type(query.parameter_types[name]),
                value,
            )
            for name, value in query.parameters.items()
        ]
        job_config = bigquery.QueryJobConfig()
        if bq_parameters:
            job_config.query_parameters = bq_parameters
        query_job = self._client.query(query.sql, job_config=job_config)
        rows = query_job.result()
        result = pl.from_arrow(rows.to_arrow())
        return cast(pl.DataFrame, result)

    def close(self) -> None:
        self._client.close()


def _bigquery_type(data_type: DataType) -> str:
    return {
        DataType.BOOLEAN: "BOOL",
        DataType.DATE: "DATE",
        DataType.NUMBER: "NUMERIC",
        DataType.STRING: "STRING",
        DataType.TIMESTAMP: "TIMESTAMP",
        DataType.TIMESTAMPTZ: "TIMESTAMP",
    }.get(data_type, "STRING")
