import sqlite3
from uuid import uuid4

from psi_jarvis.domain.corpus import Corpus
from psi_jarvis.domain.paper import Paper
from psi_jarvis.infrastructure.sqlite_corpus_repository import SQLiteCorpusRepository
from psi_jarvis.infrastructure.sqlite_paper_repository import SQLitePaperRepository


def test_sqlite_corpus_repository_persists_and_retrieves(tmp_path):
    database_path = tmp_path / "jarvis.db"
    paper_repository = SQLitePaperRepository(database_path)
    corpus_repository = SQLiteCorpusRepository(database_path)
    project_id = uuid4()
    paper_a = Paper(title="First Study", doi="10.1234/first")
    paper_b = Paper(title="Second Study", doi="10.1234/second")
    paper_repository.save(paper_a)
    paper_repository.save(paper_b)

    corpus = Corpus.create(
        project_id=project_id,
        papers=(paper_a, paper_b),
    )
    corpus_repository.save(corpus)

    stored = corpus_repository.get(corpus.corpus_id)

    assert stored == corpus
    assert stored is not None
    assert stored.papers == (paper_a, paper_b)
    assert stored.project_id == project_id


def test_sqlite_corpus_repository_returns_none_for_unknown_id(tmp_path):
    repository = SQLiteCorpusRepository(tmp_path / "jarvis.db")

    assert repository.get(uuid4()) is None


def test_sqlite_corpus_repository_lists_all(tmp_path):
    database_path = tmp_path / "jarvis.db"
    repository = SQLiteCorpusRepository(database_path)
    project_id = uuid4()
    corpus_a = Corpus.create(project_id=project_id)
    corpus_b = Corpus.create(project_id=project_id)

    repository.save(corpus_a)
    repository.save(corpus_b)

    assert repository.list_all() == (corpus_a, corpus_b)
