from __future__ import annotations

from pydantic import BaseModel

from .problems import Problem
from .project import Project
from .source_file import SourceFile


class LoadedProject(BaseModel):
    """
    A Hex semantic project loaded into memory.
    """

    project: Project
    problems: list[Problem]
    source_files: list[SourceFile]
