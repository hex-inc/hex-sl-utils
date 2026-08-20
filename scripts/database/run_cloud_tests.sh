#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "$script_dir/.env" ]]; then
  # shellcheck disable=SC1091
  set -a
  source "$script_dir/.env"
  set +a
fi

uv run --locked --all-packages --group database-cloud \
  pytest \
  packages/hex-sl-utils/tests/database \
  packages/hex-sl-utils/tests/calc/compiler/snapshot/expressions \
  -m 'database and database_cloud' \
  "$@"
