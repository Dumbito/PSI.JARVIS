from uuid import UUID

from psi_jarvis.domain import Paper


def test_paper_minimal():
    paper = Paper(title="Intelligence and memory")

    assert paper.title == "Intelligence and memory"
    assert paper.authors == ()
    assert paper.abstract is None
    assert paper.doi is None


def test_paper_complete():
    paper = Paper(
        title="Intelligence and memory",
        authors=("Author One", "Author Two"),
        abstract="Study abstract.",
        doi="10.1234/example",
        pmid="12345678",
        publication_year=2026,
        journal="Example Journal",
    )

    assert paper.title == "Intelligence and memory"
    assert paper.authors == ("Author One", "Author Two")
    assert paper.abstract == "Study abstract."
    assert paper.doi == "10.1234/example"
    assert paper.pmid == "12345678"
    assert paper.publication_year == 2026
    assert paper.journal == "Example Journal"


def test_paper_has_stable_id():
    paper = Paper(title="Test")

    assert isinstance(paper.id, UUID)


def test_paper_ids_are_unique():
    paper_a = Paper(title="Paper A")
    paper_b = Paper(title="Paper B")

    assert paper_a.id != paper_b.id


def test_paper_is_immutable():
    paper = Paper(title="Test")

    try:
        paper.title = "Changed"
    except AttributeError:
        pass
    else:
        raise AssertionError("Paper should be immutable")
