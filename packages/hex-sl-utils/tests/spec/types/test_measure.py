from typing_extensions import assert_type

from hex_sl_utils.spec.types import AggregateFuncName, Measure


def test_measure_without_optional_fields() -> None:
    # should not fail pyright type checking
    measure = Measure(id="row_count", func=AggregateFuncName.COUNT)
    assert_type(measure, Measure)
