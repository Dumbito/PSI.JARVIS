from dataclasses import dataclass
from uuid import UUID, uuid4

from psi_jarvis.domain.paper import Paper


@dataclass(frozen=True)
class Corpus:
    """Conjunto bibliográfico asociado a una revisión."""

    corpus_id: UUID
    project_id: UUID
    papers: tuple[Paper, ...] = ()

    @classmethod
    def create(
        cls,
        project_id: UUID,
        papers: tuple[Paper, ...] = (), 
    ) -> "Corpus":
        return cls(
            corpus_id=uuid4(),
            project_id=project_id,
            papers=tuple(papers),
        )

    @property
    def size(self) -> int:
        return len(self.papers)
