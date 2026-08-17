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

uv run --locked --all-packages --group database-local \
  pytest \
  packages/hex-sl-utils/tests/database \
  packages/hex-sl-utils/tests/calc/compiler/snapshot/expressions \
  -m 'database and database_local' \
  "$@"
