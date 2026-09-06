from typing import Protocol
from uuid import UUID

from psi_jarvis.domain.paper import Paper


class PaperRepository(Protocol):
    """Contrato para persistir y consultar artículos científicos."""

    def save(self, paper: Paper) -> None: ...

    def get(self, paper_id: UUID) -> Paper | None: ...

    def list_all(self) -> tuple[Paper, ...]: ...

    def delete(self, paper_id: UUID) -> None: ...
