#!/usr/bin/env bash

set -euo pipefail

cleanup() {
  if [[ "${HEX_SL_UTILS_DATABASE_KEEP_RUNNING:-}" != "1" ]]; then
    docker compose down --volumes --remove-orphans
  fi
}

trap cleanup EXIT

docker compose down --volumes --remove-orphans
docker compose up --build --wait -d

database_dialects="${HEX_SL_UTILS_DATABASE_DIALECTS:-clickhouse,duckdb,mssql,mysql,postgres,spark,trino}"

uv run --locked --all-packages --group database-local \
  pytest packages/hex-sl-utils/tests/database -m 'database and database_local' \
  --database-dialects "$database_dialects" \
  "$@"
