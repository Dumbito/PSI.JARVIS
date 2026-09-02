import pytest
from uuid import uuid4

from psi_jarvis.domain.corpus import Corpus
from psi_jarvis.domain.paper import Paper
from psi_jarvis.infrastructure.sqlite_corpus_repository import SQLiteCorpusRepository


def test_sqlite_corpus_repository_rejects_unknown_paper(tmp_path):
    repository = SQLiteCorpusRepository(tmp_path / "jarvis.db")
    corpus = Corpus.create(
        project_id=uuid4(),
        papers=(Paper(title="Unknown Study"),),
    )

    with pytest.raises(Exception):
        repository.save(corpus)
