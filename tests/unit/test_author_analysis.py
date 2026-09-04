from psi_jarvis.domain.analysis.author_analysis import AuthorAnalysis
from psi_jarvis.domain.paper import Paper


def test_author_analysis_counts_authors():
    papers = (
        Paper(title="A", authors=("Alice", "Bob")),
        Paper(title="B", authors=("Alice", "Carol")),
        Paper(title="C", authors=("Bob",)),
        Paper(title="D"),
    )

    analysis = AuthorAnalysis.from_papers(papers)

    assert analysis.total_papers == 4
    assert analysis.papers_with_authors == 3
    assert analysis.papers_without_authors == 1
    assert analysis.unique_authors == 3
    assert analysis.by_author == (("Alice", 2), ("Bob", 2), ("Carol", 1))


def test_author_analysis_coverage_rate():
    papers = (
        Paper(title="A", authors=("Alice",)),
        Paper(title="B"),
        Paper(title="C", authors=("Bob",)),
        Paper(title="D"),
    )

    analysis = AuthorAnalysis.from_papers(papers)

    assert analysis.author_coverage_rate == 0.5


def test_author_analysis_ignores_blank_author_names():
    papers = (
        Paper(title="A", authors=("   ", "Alice")),
        Paper(title="B", authors=("", "Bob")),
        Paper(title="C"),
    )

    analysis = AuthorAnalysis.from_papers(papers)

    assert analysis.papers_with_authors == 2
    assert analysis.papers_without_authors == 1
    assert analysis.unique_authors == 2
    assert analysis.by_author == (("Alice", 1), ("Bob", 1))


def test_author_analysis_empty_corpus():
    analysis = AuthorAnalysis.from_papers([])

    assert analysis.total_papers == 0
    assert analysis.papers_with_authors == 0
    assert analysis.papers_without_authors == 0
    assert analysis.unique_authors == 0
    assert analysis.by_author == ()
    assert analysis.author_coverage_rate == 0.0


def test_author_analysis_is_deterministic():
    papers = (
        Paper(title="A", authors=("Zed", "Alice")),
        Paper(title="B", authors=("Zed",)),
        Paper(title="C", authors=("Alice",)),
    )

    first = AuthorAnalysis.from_papers(papers)
    second = AuthorAnalysis.from_papers(papers)

    assert first == second
    assert first.by_author == (("Alice", 2), ("Zed", 2))


def test_author_analysis_rejects_invalid_counts():
    try:
        AuthorAnalysis(
            total_papers=-1,
            papers_with_authors=0,
            papers_without_authors=0,
            unique_authors=0,
            by_author=(),
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Negative total papers should fail")
