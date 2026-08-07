from hex_sl_utils.load.context import LoadContext
from hex_sl_utils.load.load_item import load_item
from hex_sl_utils.types import Model


def test_load_item_handles_empty_problem_scope():
    ctx = LoadContext()

    loaded = load_item(Model, {"id": "test"}, label="Model", ctx=ctx)

    assert loaded is None
    assert len(ctx.problems) == 1
    assert ctx.problems[0].cause_paths == [["test"]]
