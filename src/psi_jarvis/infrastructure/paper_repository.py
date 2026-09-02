from uuid import UUID

from psi_jarvis.domain.paper import Paper


class InMemoryPaperRepository:
    """Repositorio temporal en memoria para artículos científicos."""

    def __init__(self) -> None:
        self._papers: dict[UUID, Paper] = {}

    def save(self, paper: Paper) -> None:
        self._papers[paper.id] = paper

    def get(self, paper_id: UUID) -> Paper | None:
        return self._papers.get(paper_id)

    def list_all(self) -> tuple[Paper, ...]:
        return tuple(self._papers.values())
