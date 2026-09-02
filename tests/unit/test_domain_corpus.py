from uuid import uuid4

from psi_jarvis.domain.corpus import Corpus
from psi_jarvis.domain.paper import Paper


def test_corpus_create_assigns_identity_and_project():
    project_id = uuid4()
    papers = (
        Paper(title="Memory Study"),
        Paper(title="Intelligence Study"),
    )

    corpus = Corpus.create(project_id=project_id, papers=papers)

    assert corpus.corpus_id is not None
    assert corpus.project_id == project_id
    assert corpus.papers == papers
    assert corpus.size == 2


def test_corpus_defaults_to_empty():
    project_id = uuid4()

    corpus = Corpus.create(project_id=project_id)

    assert corpus.project_id == project_id
    assert corpus.papers == ()
    assert corpus.size == 0
