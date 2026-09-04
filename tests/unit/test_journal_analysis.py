from psi_jarvis.domain.analysis.journal_analysis import JournalAnalysis
from psi_jarvis.domain.paper import Paper


def test_journal_analysis_counts_journals():
    papers = (
        Paper(title="A", journal="Journal A"),
        Paper(title="B", journal="Journal A"),
        Paper(title="C", journal="Journal B"),
        Paper(title="D"),
    )

    analysis = JournalAnalysis.from_papers(papers)

    assert analysis.total_papers == 4
    assert analysis.papers_with_journal == 3
    assert analysis.papers_without_journal == 1
    assert analysis.unique_journals == 2
    assert analysis.by_journal == (("Journal A", 2), ("Journal B", 1))


def test_journal_analysis_coverage_rate():
    papers = (
        Paper(title="A", journal="Journal A"),
        Paper(title="B"),
        Paper(title="C", journal="Journal B"),
        Paper(title="D"),
    )

    analysis = JournalAnalysis.from_papers(papers)

    assert analysis.journal_coverage_rate == 0.5


def test_journal_analysis_ignores_blank_journals():
    papers = (
        Paper(title="A", journal="   "),
        Paper(title="B", journal="Journal A"),
    )

    analysis = JournalAnalysis.from_papers(papers)

    assert analysis.papers_with_journal == 1
    assert analysis.papers_without_journal == 1
    assert analysis.by_journal == (("Journal A", 1),)


def test_journal_analysis_empty_corpus():
    analysis = JournalAnalysis.from_papers([])

    assert analysis.total_papers == 0
    assert analysis.papers_with_journal == 0
    assert analysis.papers_without_journal == 0
    assert analysis.unique_journals == 0
    assert analysis.by_journal == ()
    assert analysis.journal_coverage_rate == 0.0


def test_journal_analysis_is_deterministic():
    papers = (
        Paper(title="A", journal="Z Journal"),
        Paper(title="B", journal="A Journal"),
        Paper(title="C", journal="Z Journal"),
    )

    first = JournalAnalysis.from_papers(papers)
    second = JournalAnalysis.from_papers(papers)

    assert first == second
    assert first.by_journal == (("A Journal", 1), ("Z Journal", 2))


def test_journal_analysis_rejects_invalid_counts():
    try:
        JournalAnalysis(
            total_papers=-1,
            papers_with_journal=0,
            papers_without_journal=0,
            unique_journals=0,
            by_journal=(),
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Negative total papers should fail")
