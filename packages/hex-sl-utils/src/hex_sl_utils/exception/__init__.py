"""Shared exception classes for hex-sl ecosystem."""

from __future__ import annotations

import inspect
from collections.abc import Iterable
from typing import Literal


class UserFacingError(Exception):
    """Error safe to show to end users.

    Subclasses that carry extra data should override __init__ to accept
    keyword-only arguments. The error_kwargs() method auto-discovers
    these from the __init__ signature for JSON serialization through
    the HTTP error wire format.

    Example::

        class MyError(UserFacingError):
            def __init__(
                self, message: str = "", *, suggestion: str | None = None, **kwargs
            ) -> None:
                super().__init__(message, **kwargs)
                self.suggestion = suggestion

        exc = MyError("bad input", suggestion="try X", details="col Y")
        exc.error_kwargs()  # {"suggestion": "try X", "details": "col Y"}
    """

    def __init__(self, message: str = "", *, details: str | None = None) -> None:
        super().__init__(message)
        self.details = details

    def error_kwargs(self) -> dict:
        """Return non-None keyword-only __init__ args for JSON serialization."""
        result: dict = {}
        for cls in type(self).__mro__:
            if cls in (Exception, BaseException, object):
                break
            init = cls.__dict__.get("__init__")
            if init is None:
                continue
            sig = inspect.signature(init)
            for name, param in sig.parameters.items():
                if param.kind == param.KEYWORD_ONLY and name not in result:
                    val = getattr(self, name, None)
                    if val is not None:
                        result[name] = val
        return result


class TypeCheckError(UserFacingError):
    """Semantic validation error (type mismatches in queries)."""


class UnsupportedByDialectError(UserFacingError):
    """Feature not supported by the target SQL dialect."""


class SemanticItemNotFoundError(UserFacingError):
    """A semantic item (dimension, measure, segment) was not found by name."""

    item_type: Literal["dimension", "measure", "segment"] | None

    def __init__(
        self,
        message: str = "",
        *,
        item_name: str | None = None,
        dataset: str | None = None,
        item_type: Literal["dimension", "measure", "segment"] | None = None,
        case_insensitive_matches: list[str] | None = None,
        details: str | None = None,
    ) -> None:
        super().__init__(message, details=details)
        self.item_name = item_name
        self.dataset = dataset
        self.item_type = item_type
        self.case_insensitive_matches = case_insensitive_matches

    @staticmethod
    def find_case_insensitive_matches(name: str, available: Iterable[str]) -> list[str]:
        """Return names from *available* that match *name* case-insensitively."""
        lower = name.lower()
        return [n for n in available if n.lower() == lower]
