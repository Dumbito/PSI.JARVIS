from uuid import uuid4

from psi_jarvis.domain.corpus import Corpus
from psi_jarvis.domain.paper import Paper
from psi_jarvis.infrastructure.sqlite_corpus_repository import SQLiteCorpusRepository
from psi_jarvis.infrastructure.sqlite_paper_repository import SQLitePaperRepository


def test_sqlite_corpus_repository_replaces_paper_membership(tmp_path):
    database_path = tmp_path / "jarvis.db"
    paper_repository = SQLitePaperRepository(database_path)
    corpus_repository = SQLiteCorpusRepository(database_path)
    project_id = uuid4()

    paper_a = Paper(title="Study A")
    paper_b = Paper(title="Study B")
    paper_c = Paper(title="Study C")

    for paper in (paper_a, paper_b, paper_c):
        paper_repository.save(paper)

    corpus = Corpus.create(
        project_id=project_id,
        papers=(paper_a, paper_b),
    )
    corpus_repository.save(corpus)

    updated_corpus = Corpus(
        corpus_id=corpus.corpus_id,
        project_id=project_id,
        papers=(paper_c, paper_a),
    )
    corpus_repository.save(updated_corpus)

    stored = corpus_repository.get(corpus.corpus_id)

    assert stored == updated_corpus
    assert stored.papers == (paper_c, paper_a)
