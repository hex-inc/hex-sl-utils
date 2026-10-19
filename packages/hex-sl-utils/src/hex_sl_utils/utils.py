from __future__ import annotations

from enum import Enum
from typing import NoReturn


class AutoName(Enum):
    @staticmethod
    def _generate_next_value_(
        name: str, start: int, count: int, last_values: list[object]
    ) -> str:
        return name.lower()

    def __repr__(self) -> str:
        """Repr that's compatible with inline-snapshot testing."""
        return f"{type(self).__qualname__}.{self.name}"


def assert_unreachable(arg: NoReturn) -> NoReturn:
    """
    Function that can't be called to assert that code paths are unreachable

    This function is used to signal to type checkers that certain code paths
    should never be executed. By using this function in an `else` clause or similar
    construct, you can ensure that all possible cases are handled exhaustively. If a new
    case is added in the future and not handled, the type checker will raise an error.

    The arg shouldn't be passed, it's there to trigger a type signature error when
    the calling path is, in fact, reachable.
    """
    raise AssertionError("Unreachable code reached")
