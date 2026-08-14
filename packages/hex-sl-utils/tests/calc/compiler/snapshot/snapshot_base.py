"""Base class for snapshot test modules."""

from __future__ import annotations

from abc import ABC, abstractmethod


class SnapshotTestBase(ABC):
    pass


class SelectionSnapshotTestBase(SnapshotTestBase):
    @classmethod
    @abstractmethod
    def get_calc_expressions(cls) -> list[str]:
        """Get the list of expressions to calculate."""
        ...


class AggregationSnapshotTestBase(SnapshotTestBase):
    @classmethod
    @abstractmethod
    def get_calc_expressions(cls) -> list[str]:
        """Get the list of expressions to calculate."""
        ...
