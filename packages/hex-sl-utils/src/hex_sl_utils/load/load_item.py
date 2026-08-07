from __future__ import annotations

from typing import Any, TypeVar, cast

from pydantic import BaseModel, ValidationError

from ..types.problems import KeyPath
from .context import LoadContext

T = TypeVar("T", bound=BaseModel)


def load_items(
    model_type: type[T],
    data: list[dict[str, Any]] | None,
    *,
    label: str,
    ctx: LoadContext,
) -> list[T]:
    if data is None or not isinstance(data, list):
        return []
    load_results = [load_item(model_type, item, label=label, ctx=ctx) for item in data]
    return [item for item in load_results if item is not None]


def load_item(
    model_type: type[T],
    data: dict[str, Any],
    *,
    label: str,
    ctx: LoadContext,
) -> T | None:
    try:
        return model_type.model_validate(data)
    except ValidationError as validation_exception:
        # ensure we report the error
        # The import is failed at this point, anything we do beyond this point
        # is just to continue to capture as many errors as possible, and to
        # convert stuff somewhat defensively
        maybe_id: str | None = data.get("id")
        maybe_name: str | None = data.get("name")
        item_problem_path: KeyPath = (
            [maybe_id] if maybe_id and maybe_id != ctx.current_problem_path[-1] else []
        )
        item_reported_label = (
            f"{label} `{maybe_id}`"
            if maybe_id
            else (
                f"{label} with name '{maybe_name}'"
                if maybe_name
                else f"{label} without an id or name"
            )
        )

        top_level_error_keys: set[str] = set()
        for err in validation_exception.errors():
            if err["type"] == "default_factory_not_called":
                continue

            locs_str = ".".join(str(loc) for loc in err["loc"])
            locs_str = f" at `{locs_str}`" if locs_str else ""

            err_conflict_keys = err.get("ctx", {}).get("conflict_keys", [])
            report_paths: list[KeyPath] = (
                [
                    [*ctx.current_problem_path, *item_problem_path, conflict_key + ":"]
                    for conflict_key in err_conflict_keys
                ]
                if err_conflict_keys
                else [[*ctx.current_problem_path, *item_problem_path]]
            )

            ctx.report_problem(
                severity="error",
                message=f"{item_reported_label}: {err['msg']}{locs_str}",
                validated_by_json_schema=(not err["type"].startswith("custom")),
                path=[],
                cause_paths=report_paths,
                impact_paths=report_paths,
            )
            if err["loc"] and isinstance(err["loc"][0], str):
                top_level_error_keys.add(err["loc"][0])

        # then, try to recover with partial overrides
        return attempt_recovery_load(model_type, data, top_level_error_keys, ctx=ctx)


def attempt_recovery_load(
    model_type: type[T],
    data: dict[str, Any],
    top_level_recovery_keys: set[str],
    *,
    ctx: LoadContext,
) -> T | None:
    if not hasattr(model_type, "validation_recovery_partial"):
        return None
    recovery_partial = cast(
        dict[str, Any],
        cast(Any, model_type).validation_recovery_partial(ctx),
    )
    # only override keys which failed; this will not fix problems with mutually
    # exclusive keys, but could recover from type errors on basic keys
    # the resultant instance may not be what the user intended, but it will
    # be valid and can proceed to later steps -- errors with these fields
    # should have already been logged
    recovery_overrides = {
        k: v for k, v in recovery_partial.items() if k in top_level_recovery_keys
    }
    recovery_payload = {**data, **recovery_overrides}

    # if the model is configured to forbid extra keys, attempt to remove them
    # from the recovery payload
    if model_type.model_config.get("extra") == "forbid":
        for extra_key in (
            k for k in top_level_recovery_keys if k not in model_type.model_fields
        ):
            recovery_payload.pop(extra_key, None)

    try:
        return model_type.model_validate(recovery_payload)
    except ValidationError:
        # couldn't recover with partial overrides, skip this whole item
        # do not re-report errors
        return None
