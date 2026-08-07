from __future__ import annotations

from typing import Any

from ..types import (
    Dimension,
    Measure,
    Model,
    Relation,
)
from .context import LoadContext
from .load_item import load_item, load_items


def load_model(
    model_data: dict[str, Any],
    *,
    ctx: LoadContext,
) -> Model | None:
    try:
        model_reporting_id = model_data.get("id", "unknown_model")
        with ctx.problem_scope(model_reporting_id):
            with ctx.problem_scope("dimensions"):
                dimensions: list[Dimension] = load_items(
                    Dimension,
                    model_data.get("dimensions"),
                    label="Dimension",
                    ctx=ctx,
                )
            with ctx.problem_scope("measures"):
                measures: list[Measure] = load_items(
                    Measure,
                    model_data.get("measures"),
                    label="Measure",
                    ctx=ctx,
                )
            with ctx.problem_scope("relations"):
                relations: list[Relation] = load_items(
                    Relation,
                    model_data.get("relations"),
                    label="Relation",
                    ctx=ctx,
                )
            return load_item(
                Model,
                {
                    **model_data,
                    "dimensions": dimensions,
                    "measures": measures,
                    "relations": relations,
                },
                label="Model",
                ctx=ctx,
            )
    except Exception as e:  # noqa: BLE001
        ctx.report_problem(
            severity="fatal",
            message="Internal error loading model",
            internal_logger_message=str(e),
            path=[],
        )
        return None
