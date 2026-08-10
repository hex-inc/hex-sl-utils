from __future__ import annotations

from typing import Any

from ..types import View
from .context import LoadContext
from .load_item import load_item


def load_view(
    view_data: dict[str, Any],
    *,
    ctx: LoadContext,
) -> View | None:
    try:
        view_reporting_id = view_data.get("id", "unknown_view")
        with ctx.problem_scope(view_reporting_id):
            return load_item(
                View,
                view_data,
                label="View",
                ctx=ctx,
            )
    except Exception as e:  # noqa: BLE001
        ctx.report_problem(
            severity="fatal",
            message="Internal error loading view",
            internal_logger_message=str(e),
            path=[],
        )
        return None
