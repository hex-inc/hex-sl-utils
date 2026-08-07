# hex-sl-utils

Typed models and loaders for Hex semantic-layer resources.

This package is in its initial development phase and is not yet published. Its
APIs may change until the first stable release.

## Features

- Pydantic models for semantic-layer projects, models, views, dimensions,
  measures, and relations.
- Project loading from YAML files with structured validation problems.
- Support for multiple SQL dialects.

## Installation

Once the package is published, install it with:

```bash
uv add hex-sl-utils

# or
python -m pip install hex-sl-utils
```

Python 3.11 or newer is required.

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

Repository development instructions are in the workspace
[`CONTRIBUTING.md`](../../CONTRIBUTING.md).

Licensed under the [Apache License 2.0](../../LICENSE).
