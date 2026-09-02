from typing import Protocol
from uuid import UUID

from psi_jarvis.domain.corpus import Corpus


class CorpusRepository(Protocol):
    """Contrato para persistir y consultar corpus bibliográficos."""

    def save(self, corpus: Corpus) -> None: ...

    def get(self, corpus_id: UUID) -> Corpus | None: ...

    def list_all(self) -> tuple[Corpus, ...]: ...
