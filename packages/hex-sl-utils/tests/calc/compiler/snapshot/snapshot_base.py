"""Base class for snapshot test modules."""

from __future__ import annotations

import inspect
import re
from abc import ABC, abstractmethod
from collections.abc import Mapping
from pathlib import Path
from typing import Any, ClassVar, Literal

import polars as pl
import polars.testing as pl_testing
import pytest
from database.driver.query import ExecutableQuery
from database.driver.registry import create_driver
from database.query_builder import build_values_query_for_df

from hex_sl_utils._vendor.sqlglot import exp
from hex_sl_utils.calc import parse_calc_expression
from hex_sl_utils.datatype import DataType
from hex_sl_utils.dialect import Dialect
from hex_sl_utils.expr import ExpressionContext

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
    def get_result_df(
        cls, dialect: Dialect, timezone: str | None = None
    ) -> pl.DataFrame:
        """Compile and execute this case through its canonical test driver."""
        query_timezone = timezone or cls.timezone
        query = cls.get_executable_query(dialect, query_timezone)
        with create_driver(dialect.name()) as driver:
            return driver.execute(query, timezone=query_timezone)

    @classmethod
    def get_executable_query(cls, dialect: Dialect, timezone: str) -> ExecutableQuery:
        raise NotImplementedError

    @classmethod
    def validate(
        cls, expected_df: pl.DataFrame, result_df: pl.DataFrame, dialect: Dialect
    ) -> None:
        """Compare a normalized database result with the retained baseline."""
        if dialect.name() == "redshift":
            expected_df = expected_df.select(
                **{
                    column.lower(): expected_df[column]
                    for column in expected_df.columns
                }
            )
        pl_testing.assert_frame_equal(
            result_df,
            expected_df,
            check_dtypes=False,
            abs_tol=1e-6,
            check_column_order=True,
        )

    @classmethod
    def get_result_df_str(cls, dialect: Dialect, timezone: str | None = None) -> str:
        """Render a database result dataframe without truncating its columns."""
        with pl.Config(tbl_cols=-1, tbl_width_chars=200):
            return str(cls.get_result_df(dialect, timezone))

    result_dialect: ClassVar[str] = "duckdb"


class SelectionSnapshotTestBase(SnapshotTestBase):
    context = ExpressionContext.PROJECTION

    @classmethod
    @abstractmethod
    def get_calc_expressions(cls) -> list[str]:
        """Get the list of expressions to calculate."""
        ...

    @classmethod
    def get_expression_input_data(cls) -> pl.DataFrame:
        raise NotImplementedError

    @classmethod
    def get_expected_df_from_input(
        cls, expression_input_data: pl.DataFrame, dialect: Dialect
    ) -> pl.DataFrame:
        raise NotImplementedError

    @classmethod
    def get_expected_df(cls, dialect: Dialect) -> pl.DataFrame:
        expression_input_data = cls.get_expression_input_data()
        return cls.get_expected_df_from_input(expression_input_data, dialect)

    @classmethod
    def get_executable_query(cls, dialect: Dialect, timezone: str) -> ExecutableQuery:
        input_data = cls.get_expression_input_data()
        input_columns = _input_columns(input_data, cls.columns)
        values_data = input_data.with_row_index("row")
        values_columns = {"row": DataType.NUMBER, **input_columns}
        values_query = build_values_query_for_df(values_data, values_columns, dialect)
        compiled = _compile_expressions(cls, dialect, timezone)
        query = (
            exp.select(
                exp.alias_(
                    exp.column("row", quoted=True),
                    "row",
                    quoted=True,
                ),
                *[
                    exp.alias_(expression.expression, f"col{index}", quoted=True)
                    for index, expression in enumerate(compiled, start=1)
                ],
            )
            .from_(values_query.subquery("input"))
            .order_by(exp.column("row", quoted=True))
        )
        result_types = {
            "row": DataType.NUMBER,
            **{
                f"col{index}": expression.data_type
                for index, expression in enumerate(compiled, start=1)
            },
        }
        return ExecutableQuery(query, {}, {}, result_types)


class AggregationSnapshotTestBase(SnapshotTestBase):
    context = ExpressionContext.AGGREGATION

    @classmethod
    @abstractmethod
    def get_calc_expressions(cls) -> list[str]:
        """Get the list of expressions to calculate."""
        ...

    @classmethod
    def get_expression_input_data(cls) -> pl.DataFrame:
        raise NotImplementedError

    @classmethod
    def get_expected_df_from_input(
        cls, expression_input_data: pl.DataFrame, dialect: Dialect
    ) -> pl.DataFrame:
        raise NotImplementedError

    @classmethod
    def get_expected_df(cls, dialect: Dialect) -> pl.DataFrame:
        expression_input_data = cls.get_expression_input_data()
        return cls.get_expected_df_from_input(expression_input_data, dialect)

    @classmethod
    def get_executable_query(cls, dialect: Dialect, timezone: str) -> ExecutableQuery:
        input_data = cls.get_expression_input_data()
        values_query = build_values_query_for_df(
            input_data, _input_columns(input_data, cls.columns), dialect
        )
        compiled = _compile_expressions(cls, dialect, timezone)
        query = exp.select(
            *[
                exp.alias_(expression.expression, f"col{index}", quoted=True)
                for index, expression in enumerate(compiled, start=1)
            ]
        ).from_(values_query.subquery("input"))
        result_types = {
            f"col{index}": expression.data_type
            for index, expression in enumerate(compiled, start=1)
        }
        return ExecutableQuery(query, {}, {}, result_types)


def _input_columns(
    input_data: pl.DataFrame,
    declared_columns: Mapping[str, DataType],
) -> dict[str, DataType]:
    missing_columns = set(declared_columns).difference(input_data.columns)
    if missing_columns:
        msg = (
            "Calc case column declarations are absent from its input dataframe: "
            f"{sorted(missing_columns)!r}"
        )
        raise ValueError(msg)
    return {
        column: declared_columns.get(column, _data_type_from_polars(dtype))
        for column, dtype in input_data.schema.items()
    }


def _data_type_from_polars(dtype: object) -> DataType:
    """Map fixture-only Polars dtypes for columns unused by the calc expression."""
    if dtype == pl.Boolean:
        return DataType.BOOLEAN
    if dtype == pl.Date:
        return DataType.DATE
    if dtype == pl.Time:
        return DataType.TIME
    if isinstance(dtype, pl.Datetime):
        return DataType.TIMESTAMPTZ if dtype.time_zone else DataType.TIMESTAMP
    if dtype == pl.String:
        return DataType.STRING
    if dtype == pl.Null:
        return DataType.NULL
    return DataType.NUMBER


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


def _compile_expressions(
    snapshot_test: type[SnapshotTestBase],
    dialect: Dialect,
    timezone: str,
) -> list[Any]:
    return [
        dialect.compile_calc_expr(
            parse_calc_expression(expression),
            context=snapshot_test.context,
            columns=snapshot_test.columns,
            timezone=timezone,
            parameters={},
            skip_mangle=True,
        )
        for expression in snapshot_test.get_calc_expressions()
    ]
