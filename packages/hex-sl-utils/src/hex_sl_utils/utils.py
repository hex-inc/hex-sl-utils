from __future__ import annotations

from enum import Enum


class AutoName(Enum):
    # Disable type checking on this method.
    # The issue with `_generate_next_value_` in enums is discussed in this GitHub
    # comment:
    # https://github.com/microsoft/pyright/issues/3742#issuecomment-1193395728.
    # The `Enum` class in Python has non-standard behaviors that are difficult to
    # capture in the a type system.
    def _generate_next_value_(name, start, count, last_values):  # type: ignore[override]  # noqa: ANN001, ANN202, N805
        return name.lower()  # type: ignore[attr-defined]

    def __repr__(self) -> str:
        """Repr that's compatible with inline-snapshot testing."""
        return f"{type(self).__qualname__}.{self.name}"
