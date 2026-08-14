from __future__ import annotations
from typing import Any
import json

from hex_sl.dialect.base import HexSLDialect
from hex_sl.dialect.utils.placeholder import PlaceholderStyle
from hex_sl.project.dataset import Dataset
from tests.driver import SqlDriver, get_env_var
from google.cloud import bigquery
from google.oauth2 import service_account
import polars as pl


class BigQueryDriver(SqlDriver):
    def __init__(self):
        driver_name = "bigquery"
        project_id = get_env_var("TEST_BIG_QUERY_PROJECT_ID", driver_name)
        acct = get_env_var("TEST_BIG_QUERY_SERVICE_ACCOUNT", driver_name)
        service_account_info = json.loads(
            # Replace \n with \\n to avoid breaking the JSON format
            acct.replace("\n", r"\n")
        )

        credentials = service_account.Credentials.from_service_account_info(
            service_account_info
        )
        self._client = bigquery.Client(project=project_id, credentials=credentials)
        self._dialect = HexSLDialect.from_name("bigquery")

    def evaluate_dataset(
        self, dataset: Dataset, parameters: dict[str, Any] = None, timezone: str = "UTC"
    ) -> pl.DataFrame:
        sql, config = dataset.sql_placeholders(
            PlaceholderStyle.AT_NAMED, dialect=self._dialect
        )
        bq_parameters = (
            [
                bigquery.ScalarQueryParameter(
                    name,
                    config.used_parameters[name].to_bigquery_parameter_type(),
                    value,
                )
                for name, value in parameters.items()
                if name in config.used_parameters
            ]
            if parameters
            else None
        )
        # Create a job config and set the query parameters
        job_config = bigquery.QueryJobConfig()
        if bq_parameters:
            job_config.query_parameters = bq_parameters

        query_job = self._client.query(sql, job_config=job_config)
        rows = query_job.result()
        result = pl.from_arrow(rows.to_arrow())
        return self.convert_timezones(result, dataset.dimensions_list, timezone)

    def __del__(self):
        if hasattr(self, "_client"):
            self._client.close()
