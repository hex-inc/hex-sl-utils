from __future__ import annotations


class CalcError(Exception):
    """Base class for user-facing calc language errors."""


class UserFacingError(CalcError):
    """An error whose message can be shown directly to a caller."""


class TypeCheckError(UserFacingError):
    """Raised when a calc expression is not type-correct."""


class UnsupportedByDialectError(UserFacingError):
    """Raised when a SQL dialect cannot compile a calc operation."""


class SemanticItemNotFoundError(UserFacingError):
    """Raised when a calc references a column absent from its schema."""

    def __init__(
        self,
        message: str,
        *,
        item_name: str,
        item_type: str,
        case_insensitive_matches: list[str] | None = None,
    ) -> None:
        super().__init__(message)
        self.item_name = item_name
        self.item_type = item_type
        self.case_insensitive_matches = case_insensitive_matches or []

    @staticmethod
    def find_case_insensitive_matches(name: str, available: set[str]) -> list[str]:
        folded_name = name.casefold()
        return sorted(item for item in available if item.casefold() == folded_name)
