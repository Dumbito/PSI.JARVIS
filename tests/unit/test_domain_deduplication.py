from datetime import datetime, timezone

from psi_jarvis.domain.bibliography import AcquisitionReceipt, BibliographicProvenance
from psi_jarvis.domain.bibliography.provenance import sha256_text
from psi_jarvis.domain.deduplication.deduplicator import PaperDeduplicator
from psi_jarvis.domain.paper import Paper


def provenance(source_key="ris"):
    receipt = AcquisitionReceipt.create(
        source_key=source_key,
        adapter_key=f"local-{source_key}",
        adapter_version="1",
        acquired_at=datetime(2026, 9, 5, tzinfo=timezone.utc),
        request_payload={"location": f"fixture.{source_key}"},
        input_content=f"fixture-{source_key}",
    )
    return BibliographicProvenance(
        receipt=receipt,
        record_ordinal=1,
        format_name="RIS",
        format_version="1",
        mapping_version="1",
        raw_record_sha256=sha256_text("record"),
    )


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


def test_deduplication_merges_provenance_without_changing_identity_or_representative():
    first_provenance = provenance()
    second_provenance = type(first_provenance)(
        receipt=provenance("csv").receipt,
        record_ordinal=2,
        format_name="RIS",
        format_version="1",
        mapping_version="1",
        raw_record_sha256="b" * 64,
    )
    result = PaperDeduplicator().deduplicate(
        (
            Paper(title="First representative", doi="10.1000/same", provenances=(first_provenance,)),
            Paper(title="Second duplicate", doi="10.1000/same", provenances=(second_provenance,)),
        )
    )

    assert result.papers[0].title == "First representative"
    assert result.papers[0].doi == "10.1000/same"
    assert result.papers[0].provenances == tuple(sorted((first_provenance, second_provenance), key=lambda item: item.key))
    assert {item.source_key for item in result.papers[0].provenances} == {"ris", "csv"}
