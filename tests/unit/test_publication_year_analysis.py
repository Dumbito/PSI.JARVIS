from psi_jarvis.domain.analysis.publication_year_analysis import PublicationYearAnalysis
from psi_jarvis.domain.paper import Paper


def test_publication_year_analysis_counts_years():
    papers = (
        Paper(title="A", publication_year=2024),
        Paper(title="B", publication_year=2024),
        Paper(title="C", publication_year=2025),
        Paper(title="D"),
    )

    analysis = PublicationYearAnalysis.from_papers(papers)

    assert analysis.total_papers == 4
    assert analysis.papers_with_year == 3
    assert analysis.papers_without_year == 1
    assert analysis.by_year == ((2024, 2), (2025, 1))


def test_publication_year_analysis_min_max():
    papers = (
        Paper(title="A", publication_year=2022),
        Paper(title="B", publication_year=2025),
        Paper(title="C", publication_year=2023),
    )

    analysis = PublicationYearAnalysis.from_papers(papers)

    assert analysis.year_min == 2022
    assert analysis.year_max == 2025


def test_publication_year_analysis_coverage_rate():
    papers = (
        Paper(title="A", publication_year=2024),
        Paper(title="B"),
        Paper(title="C", publication_year=2025),
        Paper(title="D"),
    )

    analysis = PublicationYearAnalysis.from_papers(papers)

    assert analysis.year_coverage_rate == 0.5


def test_publication_year_analysis_empty_corpus():
    analysis = PublicationYearAnalysis.from_papers([])

    assert analysis.total_papers == 0
    assert analysis.papers_with_year == 0
    assert analysis.papers_without_year == 0
    assert analysis.year_min is None
    assert analysis.year_max is None
    assert analysis.by_year == ()
    assert analysis.year_coverage_rate == 0.0


def test_publication_year_analysis_is_deterministic():
    papers = (
        Paper(title="A", publication_year=2025),
        Paper(title="B", publication_year=2023),
        Paper(title="C", publication_year=2025),
    )

    first = PublicationYearAnalysis.from_papers(papers)
    second = PublicationYearAnalysis.from_papers(papers)

    assert first == second
    assert first.by_year == ((2023, 1), (2025, 2))


def test_publication_year_analysis_rejects_invalid_counts():
    try:
        PublicationYearAnalysis(
            total_papers=-1,
            papers_with_year=0,
            papers_without_year=0,
            year_min=None,
            year_max=None,
            by_year=(),
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Negative total papers should fail")
