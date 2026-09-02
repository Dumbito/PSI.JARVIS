from psi_jarvis.domain.paper import Paper
from psi_jarvis.infrastructure.sqlite_paper_repository import SQLitePaperRepository


def test_sqlite_paper_repository_persists_and_retrieves(tmp_path):
    repository = SQLitePaperRepository(tmp_path / "jarvis.db")
    paper = Paper(
        title="Memory and Intelligence in Adults",
        authors=("John Doe", "Jane Doe"),
        abstract="Study of memory and intelligence.",
        doi="10.1234/example.doi",
        pmid="12345678",
        publication_year=2026,
        journal="Journal of Cognitive Neuroscience",
    )

    repository.save(paper)
    loaded = repository.get(paper.id)

    assert loaded == paper
    assert loaded is not None
    assert loaded.id == paper.id
    assert loaded.authors == ("John Doe", "Jane Doe")


def test_sqlite_paper_repository_returns_none_for_unknown_id(tmp_path):
    repository = SQLitePaperRepository(tmp_path / "jarvis.db")

    assert repository.get(__import__("uuid").uuid4()) is None


def test_sqlite_paper_repository_lists_all(tmp_path):
    repository = SQLitePaperRepository(tmp_path / "jarvis.db")
    paper_a = Paper(title="Paper A")
    paper_b = Paper(title="Paper B")

    repository.save(paper_a)
    repository.save(paper_b)

    assert repository.list_all() == (paper_a, paper_b)
