from __future__ import annotations

from enum import auto

from hex_sl_utils.exception import TypeCheckError
from hex_sl_utils.utils import AutoName


class ExpressionKind(AutoName):
    SCALAR = auto()
    COLUMN = auto()
    WINDOW = auto()
    AGGREGATION = auto()

    @staticmethod
    def _validate_infer_kind(kinds: list[ExpressionKind]) -> ExpressionKind:
        kinds_set = set(kinds)
        if not kinds_set:
            # Functions without args are considered scalar
            return ExpressionKind.SCALAR
        elif len(kinds_set) == 1:
            # There is a single unique kind, propagate it
            return next(iter(kinds_set))
        elif len(kinds_set) == 2:
            if (
                ExpressionKind.SCALAR in kinds_set
                and ExpressionKind.COLUMN in kinds_set
            ):
                # Mix of Scalar and Column unifies to Column
                return ExpressionKind.COLUMN
            elif (  # noqa: SIM114
                ExpressionKind.SCALAR in kinds_set
                and ExpressionKind.WINDOW in kinds_set
            ):
                return ExpressionKind.WINDOW
            elif (
                ExpressionKind.COLUMN in kinds_set
                and ExpressionKind.WINDOW in kinds_set
            ):
                return ExpressionKind.WINDOW
            elif (
                ExpressionKind.SCALAR in kinds_set
                and ExpressionKind.AGGREGATION in kinds_set
            ):
                # Mix of Scalar and AGG unifies to AGG
                return ExpressionKind.AGGREGATION
        elif (
            len(kinds_set) == 3
            and ExpressionKind.SCALAR in kinds_set
            and ExpressionKind.COLUMN in kinds_set
            and ExpressionKind.WINDOW in kinds_set
        ):
            return ExpressionKind.WINDOW
        msg = f"Cannot unify expression kinds: {kinds}"
        raise TypeCheckError(msg)
