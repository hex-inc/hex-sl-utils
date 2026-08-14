from typing import Protocol


class RecoveryContext(Protocol):
    def generate_programmatic_id(self, id_text: str) -> str: ...
