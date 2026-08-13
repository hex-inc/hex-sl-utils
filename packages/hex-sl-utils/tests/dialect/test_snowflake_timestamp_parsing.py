import pytest
from inline_snapshot import snapshot

from hex_sl_utils._vendor.sqlglot import exp
from hex_sl_utils.datatype import DataType
from hex_sl_utils.dialect.snowflake import HexSLSnowflake
from hex_sl_utils.expr import ExpressionKind, TypedSelectExpression


class TestSnowflakeTimestampParsing:
    """Test Snowflake's timestamp literal parsing with various formats."""

    @pytest.fixture
    def dialect(self):
        return HexSLSnowflake()

    def test_at_timezone_with_space_separator(self, dialect):
        """Test at_timezone with timestamp literal using space separator."""
        # Create a TRY_CAST expression with space-separated timestamp
        try_cast_expr = exp.TryCast(
            this=exp.Literal.string("2021-01-02 10:00:00"),
            to=exp.DataType.build("TIMESTAMP"),
            requires_string=True,
        )
        ts_expr = TypedSelectExpression.from_sqlglot(
            try_cast_expr, DataType.TIMESTAMP, ExpressionKind.SCALAR
        )

        result = dialect.at_timezone(ts_expr, "America/New_York")

        sql = result.expression.sql(dialect="snowflake")
        assert sql == snapshot(
            "CONVERT_TIMEZONE('America/New_York', TO_TIMESTAMP_TZ(CONCAT(TO_CHAR(CONVERT_TIMEZONE('America/New_York', 'UTC', CAST('2021-01-02 10:00:00.000000' AS TIMESTAMP)), 'YYYY-MM-DD HH24:MI:SS.FF6'), 'Z')))"
        )

    def test_at_timezone_with_t_separator(self, dialect):
        """Test at_timezone with timestamp literal using T separator (ISO 8601)."""
        try_cast_expr = exp.TryCast(
            this=exp.Literal.string("2021-01-02T10:00:00"),
            to=exp.DataType.build("TIMESTAMP"),
            requires_string=True,
        )
        ts_expr = TypedSelectExpression.from_sqlglot(
            try_cast_expr, DataType.TIMESTAMP, ExpressionKind.SCALAR
        )

        result = dialect.at_timezone(ts_expr, "UTC")

        sql = result.expression.sql(dialect="snowflake")
        assert sql == snapshot("CAST('2021-01-02T10:00:00.000000Z' AS TIMESTAMPTZ)")

    def test_at_timezone_with_milliseconds_space(self, dialect):
        """Test at_timezone with timestamp literal including milliseconds (space separator)."""
        try_cast_expr = exp.TryCast(
            this=exp.Literal.string("2021-01-02 10:00:00.123"),
            to=exp.DataType.build("TIMESTAMP"),
            requires_string=True,
        )
        ts_expr = TypedSelectExpression.from_sqlglot(
            try_cast_expr, DataType.TIMESTAMP, ExpressionKind.SCALAR
        )

        result = dialect.at_timezone(ts_expr, "Europe/London")

        sql = result.expression.sql(dialect="snowflake")
        assert sql == snapshot(
            "CONVERT_TIMEZONE('Europe/London', TO_TIMESTAMP_TZ(CONCAT(TO_CHAR(CONVERT_TIMEZONE('Europe/London', 'UTC', CAST('2021-01-02 10:00:00.123000' AS TIMESTAMP)), 'YYYY-MM-DD HH24:MI:SS.FF6'), 'Z')))"
        )

    def test_at_timezone_with_milliseconds_t_separator(self, dialect):
        """Test at_timezone with timestamp literal including milliseconds (T separator)."""
        try_cast_expr = exp.TryCast(
            this=exp.Literal.string("2021-01-02T10:00:00.456"),
            to=exp.DataType.build("TIMESTAMP"),
            requires_string=True,
        )
        ts_expr = TypedSelectExpression.from_sqlglot(
            try_cast_expr, DataType.TIMESTAMP, ExpressionKind.SCALAR
        )

        result = dialect.at_timezone(ts_expr, "Asia/Tokyo")

        sql = result.expression.sql(dialect="snowflake")
        assert sql == snapshot(
            "CONVERT_TIMEZONE('Asia/Tokyo', TO_TIMESTAMP_TZ(CONCAT(TO_CHAR(CONVERT_TIMEZONE('Asia/Tokyo', 'UTC', CAST('2021-01-02 10:00:00.456000' AS TIMESTAMP)), 'YYYY-MM-DD HH24:MI:SS.FF6'), 'Z')))"
        )

    def test_at_timezone_with_invalid_format_fallback(self, dialect):
        """Test at_timezone with invalid timestamp format falls back to general logic."""
        # Use an invalid format that won't match the regex
        try_cast_expr = exp.TryCast(
            this=exp.Literal.string("invalid-timestamp"),
            to=exp.DataType.build("TIMESTAMP"),
            requires_string=True,
        )
        ts_expr = TypedSelectExpression.from_sqlglot(
            try_cast_expr, DataType.TIMESTAMP, ExpressionKind.SCALAR
        )

        result = dialect.at_timezone(ts_expr, "UTC")

        sql = result.expression.sql(dialect="snowflake")
        # Should use general timezone logic with YEAR(), MONTH(), etc. functions
        assert sql == snapshot(
            "TO_TIMESTAMP_TZ(CONCAT(TO_CHAR(TRY_CAST('invalid-timestamp' AS TIMESTAMP), 'YYYY-MM-DD HH24:MI:SS.FF6'), 'Z'))"
        )
