from typing import Any

from inline_snapshot import snapshot

from hex_sl_utils.spec.load import load_project
from hex_sl_utils.spec.types import (
    Measure,
    ScalarExpressionDefaultBoolean,
    ScalarExpressionDefaultNumber,
)

from .utils import make_yml, snapshot_yml_load_problems, tmp_project_dir

OK_MODEL_JSON = {"id": "test_model", "base_sql_table": "test"}


def make_model_measure_yml(**kwargs: Any) -> str:
    return make_yml(
        {
            **OK_MODEL_JSON,
            "measures": [{"id": "test", **kwargs}],
        }
    )


def load_yml_model_measure(model_yml: str) -> Measure:
    with tmp_project_dir(model_yml) as project_dir:
        loaded = load_project(
            project_dir=project_dir,
            project_name="Test",
            dialect_name="duckdb",
        )
        assert loaded.problems == []
        return loaded.project.models[0].measures[0]


# ====== Basic load ======


def test_load_invalid_measure_missing_id():
    measure_json = {"func": "count"}
    yml = make_yml({**OK_MODEL_JSON, "measures": [measure_json]})
    assert snapshot_yml_load_problems(yml) == snapshot(
        "[ERROR] Measure without an id or name: Field required at `id`"
    )


def test_load_invalid_measure_missing_func():
    yml = make_model_measure_yml()
    assert snapshot_yml_load_problems(yml) == snapshot(
        "[ERROR] Measure `test`: One of `func`, `func_sql`, or `func_calc` must be provided"
    )


def test_load_measure_ok_func_count():
    yml = make_model_measure_yml(func="count")
    ds = load_yml_model_measure(yml)
    assert ds.id == "test"
    assert ds.func == "count"
    assert ds.type == "number"


def test_load_measure_ok_func_sum_of_dim():
    yml = make_model_measure_yml(func="sum", of="price")
    ds = load_yml_model_measure(yml)
    assert ds.func == "sum"
    assert ds.of == "price"
    assert ds.type == "number"


def test_load_measure_ok_func_sum_of_inline_sql_expr():
    yml = make_model_measure_yml(func="sum", of={"expr_sql": "1"})
    ds = load_yml_model_measure(yml)
    assert ds.func == "sum"
    assert ds.type == "number"
    assert isinstance(ds.of, ScalarExpressionDefaultNumber)
    assert ds.of.expr_sql == "1"
    assert ds.of.type == "number"


def test_load_measure_ok_func_filter_dim():
    yml = make_model_measure_yml(func="count", filters=["is_valid"])
    ds = load_yml_model_measure(yml)
    assert ds.filters[0] == "is_valid"


def test_load_measure_ok_func_filter_inline_sql_expr():
    yml = make_model_measure_yml(func="count", filters=[{"expr_sql": "1"}])
    ds = load_yml_model_measure(yml)
    assert isinstance(ds.filters[0], ScalarExpressionDefaultBoolean)
    assert ds.filters[0].expr_sql == "1"
    assert ds.filters[0].type == "boolean"


def test_load_measure_ok_func_sql():
    yml = make_model_measure_yml(func_sql="SUM(1)")
    ds = load_yml_model_measure(yml)
    assert ds.func_sql == "SUM(1)"
    assert ds.type == "number"


def test_load_measure_ok_func_calc():
    yml = make_model_measure_yml(func_calc="SUM(1)")
    ds = load_yml_model_measure(yml)
    assert ds.func_calc == "SUM(1)"
    assert ds.type == "number"


def test_load_measure_inferred_name():
    yml = make_model_measure_yml(id="my_measure", func="count")
    ds = load_yml_model_measure(yml)
    assert ds.id == "my_measure"
    assert ds.name == "My measure"


# ====== Problem detection ======


def test_load_invalid_measure_conflicting_func_1():
    yml = make_model_measure_yml(func="count", func_sql="SUM(1)")
    assert snapshot_yml_load_problems(yml) == snapshot(
        "[ERROR] Measure `test`: Only one of `func`, `func_sql`, or `func_calc` can be provided"
    )


def test_load_invalid_measure_conflicting_func_2():
    yml = make_model_measure_yml(func="count", func_calc="SUM(1)")
    assert snapshot_yml_load_problems(yml) == snapshot(
        "[ERROR] Measure `test`: Only one of `func`, `func_sql`, or `func_calc` can be provided"
    )


def test_load_invalid_measure_conflicting_func_3():
    yml = make_model_measure_yml(func_sql="SUM(1)", func_calc="SUM(1)")
    assert snapshot_yml_load_problems(yml) == snapshot(
        "[ERROR] Measure `test`: Only one of `func`, `func_sql`, or `func_calc` can be provided"
    )


def test_load_invalid_measure_conflicting_func_4():
    yml = make_model_measure_yml(func="count", func_sql="SUM(1)", func_calc="SUM(1)")
    assert snapshot_yml_load_problems(yml) == snapshot(
        "[ERROR] Measure `test`: Only one of `func`, `func_sql`, or `func_calc` can be provided"
    )


def test_load_invalid_measure_filters_with_func_sql():
    yml = make_model_measure_yml(func_sql="SUM(1)", filters=["is_valid"])
    assert snapshot_yml_load_problems(yml) == snapshot(
        "[ERROR] Measure `test`: `filters` is not supported when using `func_sql`"
    )


def test_load_invalid_measure_filters_with_func_calc():
    yml = make_model_measure_yml(func_calc="SUM(1)", filters=["is_valid"])
    assert snapshot_yml_load_problems(yml) == snapshot(
        "[ERROR] Measure `test`: `filters` is not supported when using `func_calc`"
    )


def test_load_invalid_measure_bad_func():
    yml = make_model_measure_yml(func="bad_func", of="price")
    assert snapshot_yml_load_problems(yml) == snapshot(
        "[ERROR] Measure `test`: Input should be 'count', 'count_distinct', 'sum', 'sum_boolean', 'avg', 'min', 'max', 'median', 'stddev', 'stddev_pop', 'variance' or 'variance_pop' at `func`"
    )


def test_load_invalid_measure_missing_of():
    yml = make_model_measure_yml(func="sum")
    assert snapshot_yml_load_problems(yml) == snapshot(
        "[ERROR] Measure `test`: `of` is required when `func` is provided and is not `count`"
    )


def test_load_invalid_measure_bad_type():
    yml = make_model_measure_yml(func_sql="1", type="bad_type")
    assert snapshot_yml_load_problems(yml) == snapshot(
        "[ERROR] Measure `test`: Input should be 'number', 'string', 'timestamp_tz', 'timestamp_naive', 'date', 'boolean', 'null' or 'other' at `type`"
    )


def test_load_invalid_measure_extra_key():
    yml = make_model_measure_yml(func="count", extra_key="extra_value")
    assert snapshot_yml_load_problems(yml) == snapshot(
        "[ERROR] Measure `test`: Extra inputs are not permitted at `extra_key`"
    )


def test_load_invalid_measure_semi_additive_pick():
    yml = make_model_measure_yml(
        func="count",
        semi_additive={"over": [{"dimension": "str", "pick": "invalid_pick"}]},
    )
    assert snapshot_yml_load_problems(yml) == snapshot(
        "[ERROR] Measure `test`: Input should be 'min' or 'max' at `semi_additive.over.0.pick`"
    )


def test_load_invalid_measure_semi_additive_over_too_many():
    yml = make_model_measure_yml(
        func="count",
        semi_additive={"over": [{"dimension": "str"}, {"dimension": "bool"}]},
    )
    assert snapshot_yml_load_problems(yml) == snapshot(
        "[ERROR] Measure `test`: List should have at most 1 item after validation, not 2 at `semi_additive.over`"
    )
