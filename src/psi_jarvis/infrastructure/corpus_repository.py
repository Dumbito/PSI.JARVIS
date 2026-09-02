from uuid import UUID

from psi_jarvis.domain.corpus import Corpus


class InMemoryCorpusRepository:
    """Repositorio temporal en memoria para corpus bibliográficos."""

    def __init__(self) -> None:
        self._corpora: dict[UUID, Corpus] = {}

    def save(self, corpus: Corpus) -> None:
        self._corpora[corpus.corpus_id] = corpus

    def get(self, corpus_id: UUID) -> Corpus | None:
        return self._corpora.get(corpus_id)

    def list_all(self) -> tuple[Corpus, ...]:
        return tuple(self._corpora.values())
