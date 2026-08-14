from __future__ import annotations


import polars as pl
from typing import TYPE_CHECKING, Any


from hex_sl.dialect.base import HexSLDialect
from hex_sl.dialect.utils.placeholder import PlaceholderStyle
from . import SqlDriver

if TYPE_CHECKING:
    from hex_sl.project.dataset import Dataset


class PolarsReadDatabaseDriver(SqlDriver):
    """
    A driver that uses the polars.read_database function.
    """

    def connection(self) -> Any:
        """
        A connection compatible with the polars.read_database function.
        """
        msg = "PolarsReadDatabaseDriver.engine method is not implemented."
        raise NotImplementedError(msg)

    @property
    def placeholder_style(self) -> PlaceholderStyle:
        msg = "PolarsReadDatabaseDriver.placeholder_style method is not implemented."
        raise NotImplementedError(msg)

    @property
    def dialect(self) -> HexSLDialect:
        msg = "PolarsReadDatabaseDriver.dialect method is not implemented."
        raise NotImplementedError(msg)

    @property
    def params_name(self) -> str:
        return "parameters"

    def execute_options(self, parameters: dict[str, Any]) -> dict[str, Any]:
        return {self.params_name: parameters}

    def evaluate_dataset(
        self,
        dataset: Dataset,
        parameters: dict[str, Any] = None,
        timezone: str = "UTC",
        *,
        skip_parameters: bool = False,
    ) -> pl.DataFrame:
        if not skip_parameters:
            sql, config = dataset.sql_placeholders(
                self.placeholder_style, dialect=self.dialect
            )
            if self.placeholder_style in [
                PlaceholderStyle.QMARK,
                PlaceholderStyle.FORMAT,
                PlaceholderStyle.NUMERIC,
                PlaceholderStyle.ASYNCPG,
            ]:
                # Positional parameters
                params = [parameters[p] for p in config.order]
            else:
                # Named parameters
                params = (
                    {
                        name: value
                        for name, value in parameters.items()
                        if name in config.used_parameters
                    }
                    if parameters
                    else {}
                )
        else:
            sql = dataset.base_sql(dialect=self.dialect)
            params = {}

        result = pl.read_database(
            sql,
            connection=self.connection(),
            execute_options=self.execute_options(params),
            infer_schema_length=100000,
        )

        return self.convert_timezones(result, dataset.dimensions_list, timezone)
