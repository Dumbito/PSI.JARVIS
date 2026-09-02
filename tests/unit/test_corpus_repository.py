from uuid import uuid4

from psi_jarvis.domain.corpus import Corpus
from psi_jarvis.domain.paper import Paper
from psi_jarvis.infrastructure.corpus_repository import InMemoryCorpusRepository


def test_in_memory_corpus_repository_persists_and_retrieves():
    repository = InMemoryCorpusRepository()
    project_id = uuid4()
    corpus = Corpus.create(
        project_id=project_id,
        papers=(Paper(title="Memory Study"),),
    )

    repository.save(corpus)

    assert repository.get(corpus.corpus_id) == corpus


def test_in_memory_corpus_repository_returns_none_for_unknown_id():
    repository = InMemoryCorpusRepository()

    assert repository.get(uuid4()) is None


def test_in_memory_corpus_repository_lists_all():
    repository = InMemoryCorpusRepository()
    project_id = uuid4()
    corpus_a = Corpus.create(project_id=project_id)
    corpus_b = Corpus.create(project_id=project_id)

    repository.save(corpus_a)
    repository.save(corpus_b)

    assert repository.list_all() == (corpus_a, corpus_b)
