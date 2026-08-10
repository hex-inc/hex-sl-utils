from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Iterator
from contextlib import contextmanager

from ..types import KeyPath, Problem, ProblemSeverity, Project

logger = logging.getLogger(__name__)


class LoadContext:
    def __init__(self) -> None:
        self.problems: list[Problem] = []
        self.current_problem_path: KeyPath = []
        self._project: Project | None = None
        self._unique_id_counter: dict[str, int] = defaultdict(int)

    @property
    def project(self) -> Project:
        if self._project is None:
            msg = "Project not initialized"
            raise ValueError(msg)
        return self._project

    @project.setter
    def project(self, project: Project) -> None:
        self._project = project

    def generate_programmatic_id(self, id_text: str) -> str:
        count = self._unique_id_counter[id_text]
        self._unique_id_counter[id_text] += 1
        return f"{id_text}_{count}"

    @contextmanager
    def problem_scope(self, *keys: str | int) -> Iterator[None]:
        self.current_problem_path.extend(keys)
        try:
            yield
        finally:
            if keys:
                del self.current_problem_path[-len(keys) :]

    def report_problem(
        self,
        severity: ProblemSeverity,
        message: str,
        *,
        path: KeyPath,
        cause_paths: list[KeyPath] | None = None,
        impact_paths: list[KeyPath] | None = None,
        validated_by_json_schema: bool = False,
        internal_logger_message: str = "",
    ) -> None:
        default_path = [*self.current_problem_path, *path]
        problem = Problem(
            severity=severity,
            message=message,
            cause_paths=cause_paths if cause_paths is not None else [default_path],
            impact_paths=impact_paths if impact_paths is not None else [default_path],
            validated_by_json_schema=validated_by_json_schema,
        )
        if severity == "fatal" or internal_logger_message:
            logger.error(
                "%s %s",
                problem.to_str(),
                internal_logger_message,
            )
        self.problems.append(problem)
