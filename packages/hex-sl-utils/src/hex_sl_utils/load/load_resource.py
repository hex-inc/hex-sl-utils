from __future__ import annotations

from typing import Any

from ..types import Resource
from ..types.resource import DEFAULT_RESOURCE_TYPE
from .context import LoadContext
from .load_model import load_model
from .load_view import load_view


def load_resource(
    resource_data: dict[str, Any],
    *,
    ctx: LoadContext,
) -> Resource | None:
    try:
        resource_type: str = resource_data.get("type", DEFAULT_RESOURCE_TYPE)
        if resource_type == "model":
            return load_model(resource_data, ctx=ctx)
        elif resource_type == "view":
            return load_view(resource_data, ctx=ctx)
        else:
            resource_reporting_id = resource_data.get("id", "unknown_resource")
            ctx.report_problem(
                severity="error",
                message=f"Unknown resource type: `{resource_type}`",
                path=[resource_reporting_id, "type"],
            )
            return None
    except Exception as e:  # noqa: BLE001
        ctx.report_problem(
            severity="fatal",
            message="Internal error loading resource",
            internal_logger_message=str(e),
            path=[],
        )
        return None
