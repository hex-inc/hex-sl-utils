from hex_sl._vendor.sqlglot import parse_one

from hex_sl.expr import has_window_function


def test_has_window1():
    expr = parse_one("mean(x) OVER (PARTITION BY y ORDER BY z)")
    assert has_window_function(expr)


def test_has_window2():
    expr = parse_one("x + 2")
    assert not has_window_function(expr)


def test_has_window3():
    expr = parse_one("(mean(x) OVER (PARTITION BY y ORDER BY z)) * 2")
    assert has_window_function(expr)


def test_has_window4():
    expr = parse_one("mean(x) * 2")
    assert not has_window_function(expr)
