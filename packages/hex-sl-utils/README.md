# hex-sl-utils

Typed models and loaders for Hex semantic-layer resources.

This package is in its initial development phase and is not yet published. Its
APIs may change until the first stable release.

## Features

- Pydantic models for semantic-layer projects, models, views, dimensions,
  measures, and relations.
- Hex calc-language parsing, serializable AST models, and SQL compilation.
- Project loading from YAML files with structured validation problems.
- Support for multiple SQL dialects.
- Generated JSON Schema and TypeScript declarations.

## Installation

Once the package is published, install it with:

```bash
uv add hex-sl-utils

# or
python -m pip install hex-sl-utils
```

Python 3.9 or newer is required.

## Usage

Load all `.yml` and `.yaml` resources beneath a project directory:

```python
from hex_sl_utils.load import load_project

loaded = load_project(
    project_dir="path/to/project",
    project_name="My project",
    dialect_name="duckdb",
)

for problem in loaded.problems:
    print(problem.to_str())

for model in loaded.project.models:
    print(model.id)
```

Converters and other callers that already hold file contents in memory can use
the equivalent `load_project_files` entry point:

```python
from hex_sl_utils.load import load_project_files

loaded = load_project_files(
    files={"orders.yml": "id: orders\nbase_sql_table: analytics.orders\n"},
    project_name="My project",
    dialect_name="duckdb",
)
```

Models are also available directly from `hex_sl_utils.types` for validation and
generation:

```python
from hex_sl_utils.types import Model

model = Model.model_validate(
    {
        "id": "orders",
        "base_sql_table": "analytics.orders",
    }
)
```

Calc formulas can be parsed without a Hex-SL project:

```python
from hex_sl_utils.calc import parse_calc_expression

calc = parse_calc_expression("sum(revenue) / count(order_id)")
print(calc.to_string())
```

Compilation is exposed through `CalcExpr.compile()` and
`compile_calc_expression()`. It accepts a `CalcDialect` adapter, a mapping of
column names to `DataType`, parameter types, and an expression context, and
returns a `TypedSelectExpression` containing the SQLGlot expression, result
type, and scalar/column/aggregation/window kind.

The adapter boundary is intentional: this package owns the calc language and
compiler, while an embedding query engine owns dialect-specific SQL behavior.
It lets Hex-SL supply its existing dialect implementation without introducing
a dependency from `hex-sl-utils` back to `hex-sl`.

The generated schema artifacts are included in the distribution and can be
read without relying on a checkout path:

```python
from hex_sl_utils.schema import resource_json_schema

schema = resource_json_schema()
```

Repository development instructions are in the workspace
[`CONTRIBUTING.md`](../../CONTRIBUTING.md).

Licensed under the [Apache License 2.0](../../LICENSE).
