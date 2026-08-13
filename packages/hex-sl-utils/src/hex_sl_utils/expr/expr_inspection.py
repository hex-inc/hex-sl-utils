from hex_sl._vendor.sqlglot import exp


def has_aggregate_function(expression: exp.Expression) -> bool:
    """
    Analyze a sqlglot expression and return whether it contains an aggregate function.

    Args:
        expression (exp.Expression): The sqlglot expression to analyze.

    Returns:
        bool: True if the expression contains an aggregate function, False otherwise.
    """
    has_agg = False

    def traverse(node: exp.Expression) -> None:
        nonlocal has_agg
        if isinstance(node, exp.AggFunc):
            has_agg = True
            return
        elif isinstance(node, exp.Anonymous):
            # Handle median
            name = str(node.this).lower()
            if "quantile" in name or "median" in name or "percentile" in name:
                has_agg = True
                return
        for child in node.iter_expressions():
            traverse(child)

    traverse(expression)
    return has_agg


def has_window_function(expression: exp.Expression) -> bool:
    """
    Analyze a sqlglot expression and return whether it contains a window function.

    Args:
        expression (exp.Expression): The sqlglot expression to analyze.

    Returns:
        bool: True if the expression contains a window function, False otherwise.
    """
    has_window = False

    def traverse(node: exp.Expression) -> None:
        nonlocal has_window
        if isinstance(node, exp.Window):
            has_window = True
            return
        for child in node.iter_expressions():
            traverse(child)

    traverse(expression)
    return has_window


def has_column_references(expression: exp.Expression) -> bool:
    """
    Analyze a sqlglot expression and return whether it contains column references.

    Args:
        expression (exp.Expression): The sqlglot expression to analyze.

    Returns:
        bool: True if the expression contains columns, False otherwise.
    """
    has_columns = False

    def traverse(node: exp.Expression) -> None:
        nonlocal has_columns
        if isinstance(node, (exp.Column, exp.Identifier)):
            has_columns = True
            return
        for child in node.iter_expressions():
            traverse(child)

    traverse(expression)
    return has_columns
