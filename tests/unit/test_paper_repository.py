from uuid import uuid4

from psi_jarvis.domain.paper import Paper
from psi_jarvis.infrastructure.paper_repository import InMemoryPaperRepository


def test_in_memory_paper_repository_persists_and_retrieves():
    repository = InMemoryPaperRepository()
    paper = Paper(title="Memory and Intelligence")

    repository.save(paper)

    assert repository.get(paper.id) == paper


def test_in_memory_paper_repository_returns_none_for_unknown_id():
    repository = InMemoryPaperRepository()

    assert repository.get(uuid4()) is None


def test_in_memory_paper_repository_lists_all():
    repository = InMemoryPaperRepository()
    paper_a = Paper(title="Paper A")
    paper_b = Paper(title="Paper B")

    repository.save(paper_a)
    repository.save(paper_b)

    assert repository.list_all() == (paper_a, paper_b)
