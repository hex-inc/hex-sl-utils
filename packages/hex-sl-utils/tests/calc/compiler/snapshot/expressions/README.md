# Calc SQL expression snapshots

Each expression test module contains one inline snapshot of its directly
compiled, pretty-printed SQL for every supported dialect. The source calcs are
listed once at the top, in compilation order.

```sh
# update inline snapshots after changing a calc case or compiler output
devbox run -- uv run --locked --all-packages pytest \
  packages/hex-sl-utils/tests/calc/compiler/snapshot/expressions \
  -m 'not database' \
  --inline-snapshot=fix
```
