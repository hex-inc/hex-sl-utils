from typing import assert_type

from hex_sl_utils.spec.types import (
    View,
    ViewContentDimensionItem,
    ViewContentMeasureItem,
    ViewContentsGroup,
)


def test_view_without_optional_fields() -> None:
    # should not fail pyright type checking
    view = View(
        id="order_view",
        base="orders",
        contents=[],
    )
    assert_type(view, View)


def test_view_contents_group_without_optional_fields() -> None:
    # should not fail pyright type checking
    view_contents_group = ViewContentsGroup(dimensions=["..."])
    assert_type(view_contents_group, ViewContentsGroup)


def test_view_content_dimension_item_without_optional_fields() -> None:
    # should not fail pyright type checking
    view_content_dimension_item = ViewContentDimensionItem(dimension="order_id")
    assert_type(view_content_dimension_item, ViewContentDimensionItem)


def test_view_content_measure_item_without_optional_fields() -> None:
    # should not fail pyright type checking
    view_content_measure_item = ViewContentMeasureItem(measure="order_id")
    assert_type(view_content_measure_item, ViewContentMeasureItem)
