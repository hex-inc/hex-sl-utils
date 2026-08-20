# Calc SQL expression snapshots

The adjacent `.sql` files record each calc's directly compiled, pretty-printed
SQL expression. The source calcs are listed once at the top, in compilation
order. The harness verifies the source list against `get_calc_expressions()`.

```sh
# update the adjacent SQL files after changing a calc case or compiler output
devbox run build:calc-sql-snapshots

# check for missing, stale, or orphaned snapshot files
devbox run verify:calc-sql-snapshots
```
