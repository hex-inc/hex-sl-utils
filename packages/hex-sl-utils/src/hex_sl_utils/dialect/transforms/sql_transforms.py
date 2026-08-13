from functools import reduce

from hex_sl_utils._vendor.sqlglot import exp, generator
from hex_sl_utils._vendor.sqlglot.helper import find_new_name


def values_as_union_with_consistent_names_sql(
    gen: generator.Generator, expression: exp.Values
) -> str:
    # Converts `VALUES...` expression into a series of select unions, where each
    # select aliases values to the desired column names.
    #
    # The default sqlglot implementation only aliases the column names in the first
    # select, which isn't supported by some dialects, like redshift.
    alias_node = expression.args.get("alias")
    column_names = alias_node and alias_node.columns

    selects: list[exp.Query] = []

    for tup in expression.expressions:
        row = tup.expressions

        if column_names:
            row = [
                exp.alias_(value, column_name)
                for value, column_name in zip(row, column_names)
            ]

        selects.append(exp.Select(expressions=row))

    query = reduce(lambda x, y: exp.union(x, y, distinct=False, copy=False), selects)
    return gen.subquery_sql(query.subquery(alias_node and alias_node.this, copy=False))


def hex_sl_eliminate_qualify(expression: exp.Expression) -> exp.Expression:
    """
    Custom QUALIFY elimination with groupby handling
    """
    if isinstance(expression, exp.Select) and expression.args.get("qualify"):
        # 1. Ensure all selects have aliases
        for select in expression.selects:
            if not select.alias_or_name:
                select.replace(
                    exp.alias_(select, find_new_name(expression.named_selects, "_c"))
                )

        # 2. Process QUALIFY filters
        qualify_filter = expression.args["qualify"].pop().this
        for node in qualify_filter.find_all(exp.Window, exp.Column):
            if isinstance(node, exp.Window):
                # Add window function with generated alias
                alias = find_new_name(expression.named_selects, "_w")
                expression.select(exp.alias_(node, alias), copy=False)
                node.replace(exp.column(alias))

        # 3. Build final transformed query
        return (
            exp.select("*")
            .from_(expression.subquery("_t", copy=False), copy=False)
            .where(qualify_filter, copy=False)
        )

    return expression
