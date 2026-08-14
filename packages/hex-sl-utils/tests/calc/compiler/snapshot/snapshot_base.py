"""Base class for snapshot test modules."""

from __future__ import annotations

import inspect
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, Literal

import pytest

from hex_sl_utils.calc import parse_calc_expression
from hex_sl_utils.datatype import DataType
from hex_sl_utils.dialect import Dialect
from hex_sl_utils.expr import ExpressionContext

if TYPE_CHECKING:
    import polars as pl
    from hex_sl.dialect.base import HexSLDialect

DIALECT_NAMES = (
    "bigquery",
    "clickhouse",
    "duckdb",
    "mssql",
    "mysql",
    "postgres",
    "redshift",
    "snowflake",
    "spark",
    "trino",
)

SupportMethod = Literal[
    "supports_median",
    "supports_percentile_approx",
    "supports_percentile_exact",
]


class SnapshotTestBase(ABC):
    __test__: ClassVar[bool] = False
    columns: ClassVar[dict[str, DataType]]
    context: ClassVar[ExpressionContext]
    support_method: ClassVar[SupportMethod | None] = None
    timezone: ClassVar[str] = "UTC"

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        cls.__test__ = cls.__name__ == "SnapshotTest"

    @classmethod
    def get_calc_expressions(cls) -> list[str]:
        raise NotImplementedError

    @classmethod
    def supports_dialect(cls, dialect: Dialect) -> bool:
        return cls.support_method is None or getattr(dialect, cls.support_method)()

    @classmethod
    def compile_sql(cls, dialect_name: str) -> list[str]:
        dialect = Dialect.from_name(dialect_name)
        if not cls.supports_dialect(dialect):
            pytest.skip(f"{cls.support_method} is not supported by {dialect_name}")

        return [
            dialect.compile_calc_expr(
                parse_calc_expression(expression),
                context=cls.context,
                columns=cls.columns,
                timezone=cls.timezone,
                parameters={},
                skip_mangle=True,
            ).expression.sql(dialect=dialect.sqlglot_dialect(), pretty=True)
            for expression in cls.get_calc_expressions()
        ]

    @classmethod
    def render_sql_snapshot(cls) -> str:
        return _render_sql_snapshot(cls)

    @classmethod
    def get_expected_sql(cls) -> dict[str, list[str]]:
        snapshot_path = Path(inspect.getfile(cls)).with_suffix(".sql")
        snapshot_calc_expressions, snapshot = _parse_sql_snapshot(
            snapshot_path.read_text()
        )
        calc_expressions = cls.get_calc_expressions()

        if snapshot_calc_expressions != calc_expressions:
            raise ValueError(
                f"Calc expressions in {snapshot_path} do not match "
                "get_calc_expressions()"
            )

        for dialect_name, cases in snapshot.items():
            if len(cases) != len(calc_expressions):
                raise ValueError(
                    f"SQL expressions in {snapshot_path} [{dialect_name}] "
                    "do not match the calc expression count"
                )

        return snapshot

    @pytest.mark.parametrize("dialect_name", DIALECT_NAMES)
    def test_sql(self, dialect_name: str) -> None:
        assert self.compile_sql(dialect_name) == self.get_expected_sql()[dialect_name]

    @classmethod
    @abstractmethod
    def get_expected_df(cls, dialect: HexSLDialect) -> pl.DataFrame:
        """Get the expected results dataframe (computed in polars).

        Returns:
            pl.DataFrame: The expected results for validation
        """
        ...

    @classmethod
    def validate(
        cls, expected_df: pl.DataFrame, result_df: pl.DataFrame, dialect: HexSLDialect
    ) -> None:
        """Validate the query results against expected values.

        This provides a default implementation using polars frame comparison.
        Subclasses can override this for custom validation logic.

        Args:
            expected_df: The expected results dataframe
            result_df: The actual results from executing the query
            dialect: The SQL dialect that was used
        """
        import polars.testing as pl_testing
        from hex_sl.dialect.redshift import HexSLRedshift

        # Handle Redshift column name lowercasing
        if isinstance(dialect, HexSLRedshift):
            # Redshift returns column names in lowercase
            expected_df = expected_df.select(
                **{col.lower(): expected_df[col] for col in expected_df.columns}
            )

        print(dialect.name())
        pl_testing.assert_frame_equal(
            result_df,
            expected_df,
            check_dtypes=False,
            atol=1e-6,
            check_column_order=True,
        )


class SelectionSnapshotTestBase(SnapshotTestBase):
    context = ExpressionContext.PROJECTION

    @classmethod
    @abstractmethod
    def get_calc_expressions(cls) -> list[str]:
        """Get the list of expressions to calculate."""
        ...

    @classmethod
    @abstractmethod
    def get_expression_input_data(cls) -> pl.DataFrame:
        """Get the test data for the expression test."""
        ...

    @classmethod
    @abstractmethod
    def get_expected_df_from_input(
        cls, expression_input_data: pl.DataFrame, dialect: HexSLDialect
    ) -> pl.DataFrame:
        """Get the expected results dataframe from input data (computed in polars).

        Args:
            expression_input_data: The input data for the expressions
            dialect: The SQL dialect being tested

        Returns:
            pl.DataFrame: The expected results for validation
        """
        ...

    @classmethod
    def get_expected_df(cls, dialect: HexSLDialect) -> pl.DataFrame:
        """Get the expected results dataframe (computed in polars).

        Returns:
            pl.DataFrame: The expected results for validation
        """
        expression_input_data = cls.get_expression_input_data()
        return cls.get_expected_df_from_input(expression_input_data, dialect)


class AggregationSnapshotTestBase(SnapshotTestBase):
    context = ExpressionContext.AGGREGATION

    @classmethod
    @abstractmethod
    def get_calc_expressions(cls) -> list[str]:
        """Get the list of expressions to calculate."""
        ...

    @classmethod
    @abstractmethod
    def get_expression_input_data(cls) -> pl.DataFrame:
        """Get the test data for the expression test."""
        ...

    @classmethod
    @abstractmethod
    def get_expected_df_from_input(
        cls, expression_input_data: pl.DataFrame, dialect: HexSLDialect
    ) -> pl.DataFrame:
        """Get the expected results dataframe from input data (computed in polars).

        Args:
            expression_input_data: The input data for the expressions
            dialect: The SQL dialect being tested

        Returns:
            pl.DataFrame: The expected results for validation
        """
        ...

    @classmethod
    def get_expected_df(cls, dialect: HexSLDialect) -> pl.DataFrame:
        """Get the expected results dataframe (computed in polars).

        Returns:
            pl.DataFrame: The expected results for validation
        """
        expression_input_data = cls.get_expression_input_data()
        return cls.get_expected_df_from_input(expression_input_data, dialect)


_DIALECT_HEADER = re.compile(r"^-- === ([A-Z0-9_]+) ===$")
_CALC_DEFINITION = re.compile(r"^-- (.*)$")


def _parse_sql_snapshot(snapshot: str) -> tuple[list[str], dict[str, list[str]]]:
    calc_expressions: list[str] = []
    parsed: dict[str, list[str]] = {}
    dialect_name: str | None = None
    in_calc_section = False
    sql_lines: list[str] = []

    def finish_expression() -> None:
        nonlocal sql_lines
        if dialect_name is None:
            raise ValueError("SQL expression appears before a dialect section")
        parsed[dialect_name].append("\n".join(sql_lines).strip())
        sql_lines = []

    for line in snapshot.splitlines():
        dialect_match = _DIALECT_HEADER.fullmatch(line)
        if dialect_match:
            if sql_lines:
                raise ValueError("SQL expression is missing a semicolon")
            next_dialect_name = dialect_match.group(1).lower()
            if next_dialect_name == "calcs":
                if calc_expressions or parsed:
                    raise ValueError("Calc definitions must appear once at the top")
                dialect_name = None
                in_calc_section = True
                continue
            if next_dialect_name in parsed:
                raise ValueError(f"Duplicate dialect section: {next_dialect_name}")
            parsed[next_dialect_name] = []
            dialect_name = next_dialect_name
            in_calc_section = False
            continue

        calc_match = _CALC_DEFINITION.fullmatch(line)
        if calc_match and in_calc_section:
            calc_expressions.append(calc_match.group(1))
            continue

        if dialect_name is not None:
            if not line.strip() and not sql_lines:
                continue
            if line.endswith(";"):
                sql_lines.append(line[:-1])
                finish_expression()
            else:
                sql_lines.append(line)
            continue

        if line.strip():
            raise ValueError(f"Unexpected snapshot content: {line}")

    if sql_lines:
        raise ValueError("SQL expression is missing a semicolon")
    if not calc_expressions:
        raise ValueError("Snapshot does not define any calc expressions")
    return calc_expressions, parsed


def _render_sql_snapshot(snapshot_test: type[SnapshotTestBase]) -> str:
    calc_expressions = snapshot_test.get_calc_expressions()
    lines = ["-- === CALCS ==="]
    for calc_expression in calc_expressions:
        if "\n" in calc_expression:
            raise ValueError(f"Multiline calc expression: {calc_expression!r}")
        lines.append(f"-- {calc_expression}")

    for dialect_name in DIALECT_NAMES:
        dialect = Dialect.from_name(dialect_name)
        if not snapshot_test.supports_dialect(dialect):
            continue

        lines.extend(["", f"-- === {dialect_name.upper()} ==="])
        for sql in snapshot_test.compile_sql(dialect_name):
            sql_lines = sql.splitlines()
            if not sql_lines:
                raise ValueError("Empty SQL expression")
            if any(line.endswith(";") for line in sql_lines):
                raise ValueError(f"SQL collides with the semicolon delimiter: {sql!r}")
            sql_lines[-1] += ";"
            lines.extend(sql_lines)

    return "\n".join(lines) + "\n"
