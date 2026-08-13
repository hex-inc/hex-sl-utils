import pytest
from hex_sl._vendor.sqlglot import exp, parse_one
from hex_sl.datatype import DataType, datatype_to_sqlglot
from hex_sl.dialect import PlaceholderConfig, PlaceholderStyle, set_placeholder_style
from hex_sl.dialect.base import HexSLDialect
from inline_snapshot import snapshot


@pytest.fixture
def parameter_types():
    return {
        "foo": DataType.NUMBER,
        "bar": DataType.NUMBER,
        "baz": DataType.NUMBER,
        "unused": DataType.STRING,
    }


@pytest.fixture
def query_str():
    return "SELECT {{foo}}, {{bar}} + {{baz}} * {{foo}}"


@pytest.mark.parametrize("dialect_name", HexSLDialect.all_dialects)
def test_default_placeholder_parse_roundtrip(dialect_name: str):
    dialect = HexSLDialect.from_name(dialect_name)
    assert dialect is not None

    parsed = parse_one("SELECT {{foo}}", dialect=dialect.sqlglot_dialect())
    assert parsed.sql(dialect=dialect.sqlglot_dialect()) == snapshot("SELECT {{foo}}")


@pytest.mark.parametrize("dialect_name", HexSLDialect.all_dialects)
def test_placeholder_mode_qmark(dialect_name: str, parameter_types, query_str):
    dialect = HexSLDialect.from_name(dialect_name)
    assert dialect is not None

    with set_placeholder_style(PlaceholderStyle.QMARK, parameter_types) as config:
        parsed = parse_one(
            query_str,
            dialect=dialect.sqlglot_dialect(),
        )
        assert parsed.sql(dialect=dialect.sqlglot_dialect()) == snapshot(
            "SELECT ?1, ?2 + ?3 * ?4"
        )

    assert config == snapshot(
        PlaceholderConfig(
            mode=PlaceholderStyle.QMARK,
            all_parameters={
                "bar": DataType.NUMBER,
                "baz": DataType.NUMBER,
                "foo": DataType.NUMBER,
                "unused": DataType.STRING,
            },
            used_parameters={
                "foo": DataType.NUMBER,
                "bar": DataType.NUMBER,
                "baz": DataType.NUMBER,
            },
            order=["foo", "bar", "baz", "foo"],
        )
    )

    # Now back to the default
    assert parsed.sql(dialect=dialect.sqlglot_dialect()) == snapshot(
        "SELECT {{foo}}, {{bar}} + {{baz}} * {{foo}}"
    )


@pytest.mark.parametrize("dialect_name", HexSLDialect.all_dialects)
def test_placeholder_mode_format(dialect_name: str, parameter_types, query_str):
    dialect = HexSLDialect.from_name(dialect_name)
    assert dialect is not None

    with set_placeholder_style(PlaceholderStyle.FORMAT, parameter_types) as config:
        parsed = parse_one(
            query_str,
            dialect=dialect.sqlglot_dialect(),
        )
        assert parsed.sql(dialect=dialect.sqlglot_dialect()) == snapshot(
            "SELECT %s1, %s2 + %s3 * %s4"
        )

    assert config == snapshot(
        PlaceholderConfig(
            mode=PlaceholderStyle.FORMAT,
            all_parameters={
                "bar": DataType.NUMBER,
                "baz": DataType.NUMBER,
                "foo": DataType.NUMBER,
                "unused": DataType.STRING,
            },
            used_parameters={
                "foo": DataType.NUMBER,
                "bar": DataType.NUMBER,
                "baz": DataType.NUMBER,
            },
            order=["foo", "bar", "baz", "foo"],
        )
    )


@pytest.mark.parametrize("dialect_name", HexSLDialect.all_dialects)
def test_placeholder_mode_numeric(dialect_name: str, parameter_types, query_str):
    dialect = HexSLDialect.from_name(dialect_name)
    assert dialect is not None

    with set_placeholder_style(PlaceholderStyle.NUMERIC, parameter_types) as config:
        parsed = parse_one(
            query_str,
            dialect=dialect.sqlglot_dialect(),
        )
        assert parsed.sql(dialect=dialect.sqlglot_dialect()) == snapshot(
            "SELECT :1, :2 + :3 * :1"
        )

    assert config == snapshot(
        PlaceholderConfig(
            mode=PlaceholderStyle.NUMERIC,
            all_parameters={
                "bar": DataType.NUMBER,
                "baz": DataType.NUMBER,
                "foo": DataType.NUMBER,
                "unused": DataType.STRING,
            },
            used_parameters={
                "foo": DataType.NUMBER,
                "bar": DataType.NUMBER,
                "baz": DataType.NUMBER,
            },
            order=["foo", "bar", "baz"],
        )
    )


@pytest.mark.parametrize("dialect_name", HexSLDialect.all_dialects)
def test_placeholder_mode_asyncpg(dialect_name: str, parameter_types, query_str):
    dialect = HexSLDialect.from_name(dialect_name)
    assert dialect is not None

    with set_placeholder_style(PlaceholderStyle.ASYNCPG, parameter_types) as config:
        parsed = parse_one(
            query_str,
            dialect=dialect.sqlglot_dialect(),
        )
        assert parsed.sql(dialect=dialect.sqlglot_dialect()) == snapshot(
            "SELECT $1, $2 + $3 * $1"
        )

    assert config == snapshot(
        PlaceholderConfig(
            mode=PlaceholderStyle.ASYNCPG,
            all_parameters={
                "bar": DataType.NUMBER,
                "baz": DataType.NUMBER,
                "foo": DataType.NUMBER,
                "unused": DataType.STRING,
            },
            used_parameters={
                "foo": DataType.NUMBER,
                "bar": DataType.NUMBER,
                "baz": DataType.NUMBER,
            },
            order=["foo", "bar", "baz"],
        )
    )


@pytest.mark.parametrize("dialect_name", HexSLDialect.all_dialects)
def test_placeholder_mode_named(dialect_name: str, parameter_types, query_str):
    dialect = HexSLDialect.from_name(dialect_name)
    assert dialect is not None

    with set_placeholder_style(PlaceholderStyle.COLON_NAMED, parameter_types) as config:
        parsed = parse_one(
            query_str,
            dialect=dialect.sqlglot_dialect(),
        )
        assert parsed.sql(dialect=dialect.sqlglot_dialect()) == snapshot(
            "SELECT :foo, :bar + :baz * :foo"
        )

    assert config == snapshot(
        PlaceholderConfig(
            mode=PlaceholderStyle.COLON_NAMED,
            all_parameters={
                "bar": DataType.NUMBER,
                "baz": DataType.NUMBER,
                "foo": DataType.NUMBER,
                "unused": DataType.STRING,
            },
            used_parameters={
                "foo": DataType.NUMBER,
                "bar": DataType.NUMBER,
                "baz": DataType.NUMBER,
            },
            order=[],
        )
    )


@pytest.mark.parametrize("dialect_name", HexSLDialect.all_dialects)
def test_placeholder_mode_pyformat(dialect_name: str, parameter_types, query_str):
    dialect = HexSLDialect.from_name(dialect_name)
    assert dialect is not None

    with set_placeholder_style(PlaceholderStyle.PYFORMAT, parameter_types) as config:
        parsed = parse_one(
            query_str,
            dialect=dialect.sqlglot_dialect(),
        )
        assert parsed.sql(dialect=dialect.sqlglot_dialect()) == snapshot(
            "SELECT %(foo)s, %(bar)s + %(baz)s * %(foo)s"
        )

    assert config == snapshot(
        PlaceholderConfig(
            mode=PlaceholderStyle.PYFORMAT,
            all_parameters={
                "bar": DataType.NUMBER,
                "baz": DataType.NUMBER,
                "foo": DataType.NUMBER,
                "unused": DataType.STRING,
            },
            used_parameters={
                "foo": DataType.NUMBER,
                "bar": DataType.NUMBER,
                "baz": DataType.NUMBER,
            },
            order=[],
        )
    )


@pytest.mark.parametrize("dialect_name", HexSLDialect.all_dialects)
def test_placeholder_mode_clickhouse(dialect_name: str, parameter_types, query_str):
    dialect = HexSLDialect.from_name(dialect_name)
    assert dialect is not None

    expected_type = datatype_to_sqlglot(DataType.NUMBER).sql(
        dialect=dialect.sqlglot_dialect()
    )

    with set_placeholder_style(PlaceholderStyle.CLICKHOUSE, parameter_types) as config:
        parsed = parse_one(
            query_str,
            dialect=dialect.sqlglot_dialect(),
        )
        assert (
            parsed.sql(dialect=dialect.sqlglot_dialect())
            == f"SELECT {{foo: {expected_type}}}, {{bar: {expected_type}}} + {{baz: {expected_type}}} * {{foo: {expected_type}}}"
        )

    assert config == snapshot(
        PlaceholderConfig(
            mode=PlaceholderStyle.CLICKHOUSE,
            all_parameters={
                "bar": DataType.NUMBER,
                "baz": DataType.NUMBER,
                "foo": DataType.NUMBER,
                "unused": DataType.STRING,
            },
            used_parameters={
                "foo": DataType.NUMBER,
                "bar": DataType.NUMBER,
                "baz": DataType.NUMBER,
            },
            order=[],
        )
    )


@pytest.mark.parametrize("dialect_name", HexSLDialect.all_dialects)
def test_semantic_placeholder_simple(dialect_name: str):
    """Test ${foo} semantic placeholder parse and round-trip."""
    dialect = HexSLDialect.from_name(dialect_name)
    assert dialect is not None

    parsed = parse_one("SELECT ${foo}", dialect=dialect.sqlglot_dialect())

    # Verify placeholder was parsed
    placeholders = list(parsed.find_all(exp.Placeholder))
    assert len(placeholders) == 1
    assert placeholders[0].this == "foo"
    assert placeholders[0].args.get("kind") == "semantic"

    # Verify round-trip
    assert parsed.sql(dialect=dialect.sqlglot_dialect()) == snapshot("SELECT ${foo}")


@pytest.mark.parametrize("dialect_name", HexSLDialect.all_dialects)
def test_semantic_placeholder_dotted(dialect_name: str):
    """Test ${dataset.column} semantic placeholder with dotted notation."""
    dialect = HexSLDialect.from_name(dialect_name)
    assert dialect is not None

    parsed = parse_one("SELECT ${dataset.column}", dialect=dialect.sqlglot_dialect())

    placeholders = list(parsed.find_all(exp.Placeholder))
    assert len(placeholders) == 1
    assert placeholders[0].this == "dataset.column"
    assert placeholders[0].args.get("kind") == "semantic"

    # Verify round-trip
    assert parsed.sql(dialect=dialect.sqlglot_dialect()) == snapshot(
        "SELECT ${dataset.column}"
    )


@pytest.mark.parametrize("dialect_name", HexSLDialect.all_dialects)
def test_mixed_placeholders(dialect_name: str):
    """Test mixing ${...} semantic placeholders with {{...}} query param placeholders."""
    dialect = HexSLDialect.from_name(dialect_name)
    assert dialect is not None

    parsed = parse_one(
        "SELECT ${semantic_ref}, {{query_param}}", dialect=dialect.sqlglot_dialect()
    )

    placeholders = list(parsed.find_all(exp.Placeholder))
    assert len(placeholders) == 2

    # Find semantic and query param placeholders
    semantic_ph = [p for p in placeholders if p.args.get("kind") == "semantic"]
    query_ph = [p for p in placeholders if p.args.get("kind") is None]

    assert len(semantic_ph) == 1
    assert semantic_ph[0].this == "semantic_ref"

    assert len(query_ph) == 1
    # Query param placeholder uses Identifier as `this`
    assert isinstance(query_ph[0].this, exp.Identifier)
    assert query_ph[0].this.name == "query_param"

    # Verify round-trip
    assert parsed.sql(dialect=dialect.sqlglot_dialect()) == snapshot(
        "SELECT ${semantic_ref}, {{query_param}}"
    )
