from psi_jarvis.domain.deduplication.deduplicator import PaperDeduplicator
from psi_jarvis.domain.paper import Paper


def test_deduplicator_exists():
    assert PaperDeduplicator() is not None


def test_deduplicator_removes_duplicate_doi():
    papers = [
        Paper(title="Paper A", doi="10.1234/abc"),
        Paper(title="Paper B", doi="10.1234/abc"),
    ]

    result = PaperDeduplicator().deduplicate(papers)

    assert len(result.papers) == 1
    assert result.duplicates_removed == 1


def test_deduplicator_removes_duplicate_pmid():
    papers = [
        Paper(title="Paper A", pmid="123456"),
        Paper(title="Paper B", pmid="123456"),
    ]

    result = PaperDeduplicator().deduplicate(papers)

    assert len(result.papers) == 1
    assert result.duplicates_removed == 1


def test_deduplicator_removes_duplicate_title():
    papers = [
        Paper(title="Memory   and Intelligence"),
        Paper(title="Memory and Intelligence"),
    ]

    result = PaperDeduplicator().deduplicate(papers)

    assert len(result.papers) == 1
    assert result.duplicates_removed == 1


def test_deduplicator_keeps_unique_papers():
    papers = [
        Paper(title="Paper A", doi="10.1234/a"),
        Paper(title="Paper B", doi="10.1234/b"),
    ]

    result = PaperDeduplicator().deduplicate(papers)

    assert len(result.papers) == 2
    assert result.duplicates_removed == 0


def test_deduplication_preserves_order():
    papers = [
        Paper(title="First", doi="10.1234/a"),
        Paper(title="Duplicate", doi="10.1234/a"),
        Paper(title="Second", doi="10.1234/b"),
    ]

    result = PaperDeduplicator().deduplicate(papers)

    assert [paper.title for paper in result.papers] == ["First", "Second"]


def test_deduplication_statistics():
    papers = [
        Paper(title="A", doi="10.1/a"),
        Paper(title="A duplicate", doi="10.1/a"),
        Paper(title="B", doi="10.1/b"),
    ]

    result = PaperDeduplicator().deduplicate(papers)

    assert result.total_input == 3
    assert result.unique_papers == 2
    assert result.duplicates_removed == 1
