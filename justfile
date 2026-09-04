check: lint format-check type-check

fix: lint-fix format

ci: setup check test verify-artifacts build-packages smoke-test-packages

# ---
# Setup

setup: setup-uv setup-pnpm

setup-uv:
    uv sync --locked --all-packages

setup-pnpm:
    pnpm install --frozen-lockfile

# ---
# Build

build: build-packages build-artifacts

build-packages: build-packages-python

build-packages-python:
    uv build --all-packages --no-sources

# ---
# Format

format: format-python format-markdown format-typescript format-json

format-python:
    uv run --locked --all-packages ruff format

format-markdown:
    uv run --locked --all-packages rumdl fmt

format-typescript:
    oxfmt --write --no-error-on-unmatched-pattern '**/*.{ts,tsx,mts,cts}'

format-json:
    oxfmt --write --no-error-on-unmatched-pattern '**/*.{json,jsonc}'

format-check: format-check-python format-check-markdown format-check-typescript format-check-json

format-check-python:
    uv run --locked --all-packages ruff format --check

format-check-markdown:
    uv run --locked --all-packages rumdl fmt --check

format-check-typescript:
    oxfmt --check --no-error-on-unmatched-pattern '**/*.{ts,tsx,mts,cts}'

format-check-json:
    oxfmt --check --no-error-on-unmatched-pattern '**/*.{json,jsonc}'

# ---
# Lint

lint: lint-python lint-markdown lint-typescript

lint-python: 
    uv run --locked --all-packages ruff check

lint-markdown:
    uv run --locked --all-packages rumdl check

lint-typescript:
    oxlint . --deny-warnings --no-error-on-unmatched-pattern

lint-fix: lint-fix-python lint-fix-markdown lint-fix-typescript

lint-fix-python: 
    uv run --locked --all-packages ruff check --fix

lint-fix-markdown:
    uv run --locked --all-packages rumdl check --fix

lint-fix-typescript:
    oxlint . --fix --deny-warnings --no-error-on-unmatched-pattern


# ---
# Type Check

type-check: type-check-python type-check-typescript

type-check-python:
    uv run --locked --all-packages pyright

type-check-typescript:
    pnpm --recursive --if-present run check

# ---
# Test

test: test-packages test-workspace test-database-local test-database-cloud

test-packages: test-python-packages

test-python-packages:
    uv run --locked --all-packages pytest packages -m 'not database'

test-workspace: test-python-workspace

test-python-workspace:
    uv run --locked --all-packages pytest tests -m 'not database'

# ---
# Test Coverage
test-cov: test-cov-python

test-cov-python:
    uv run --locked --all-packages pytest packages tests -m 'not database' --cov=packages --cov-report=term-missing --cov-report=xml

# ---
# Smoke Test


smoke-test: smoke-test-packages

smoke-test-packages *args:
    uv run --locked --all-packages python scripts/smoke_test_packages.py {{args}}

# ---
# Artifacts

verify-artifacts: verify-schema verify-timezones verify-vendoring verify-calc-parser

build-artifacts: build-schema build-timezones build-vendoring build-calc-parser

build-schema:
    uv run --locked --all-packages python scripts/spec-schema/generate_schema.py

verify-schema:
    uv run --locked --all-packages python scripts/spec-schema/check_generated_schema.py

build-timezones:
    uv run --locked --all-packages python scripts/timezones/generate_iana_to_windows.py

verify-timezones:
    uv run --locked --all-packages python scripts/timezones/generate_iana_to_windows.py --check

build-vendoring:
    uv run --locked --all-packages python scripts/vendoring/vendor_sqlglot.py

verify-vendoring:
    uv run --locked --all-packages python scripts/vendoring/check_vendored_sqlglot.py

build-calc-parser:
    uv run --locked --all-packages python scripts/calc-parser/generate_standalone_parser.py

verify-calc-parser:
    uv run --locked --all-packages python scripts/calc-parser/check_standalone_parser.py

# ---
# Database

check-database: check-database-local check-database-cloud

check-database-local:
    uv run --locked --all-packages --group database-local pyright --project pyrightconfig.database.local.json

check-database-cloud:
    uv run --locked --all-packages --group database-cloud pyright --project pyrightconfig.database.cloud.json

test-database: test-database-local test-database-cloud

test-database-local *args:
    bash scripts/database/run_local_tests.sh {{args}}

test-database-cloud *args:
    bash scripts/database/run_cloud_tests.sh {{args}}

database-local-up:
    docker compose down --volumes --remove-orphans
    docker compose up --build --wait -d

database-local-down:
    docker compose down --volumes --remove-orphans

database-local-smoke *args:
    bash scripts/database/run_local_tests.sh -k connection_smoke {{args}}
