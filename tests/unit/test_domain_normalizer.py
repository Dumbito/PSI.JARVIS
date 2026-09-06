from datetime import datetime, timezone

from psi_jarvis.domain.bibliography import AcquisitionReceipt, BibliographicProvenance
from psi_jarvis.domain.bibliography.provenance import sha256_text
from psi_jarvis.domain.normalization.normalizer import PaperNormalizer
from psi_jarvis.domain.paper import Paper


def provenance():
    receipt = AcquisitionReceipt.create(
        source_key="ris",
        adapter_key="local-ris",
        adapter_version="1",
        acquired_at=datetime(2026, 9, 5, tzinfo=timezone.utc),
        request_payload={"location": "fixture.ris"},
        input_content="fixture",
    )
    return BibliographicProvenance(
        receipt=receipt,
        record_ordinal=1,
        format_name="RIS",
        format_version="1",
        mapping_version="1",
        raw_record_sha256=sha256_text("record"),
    )


def test_normalizer_exists():
    assert PaperNormalizer() is not None


def test_normalizer_normalizes_title():
    paper = Paper(title="  Memory   and   Intelligence  ")

    result = PaperNormalizer().normalize(paper)

    assert result.title == "Memory and Intelligence"


def test_normalizer_normalizes_authors():
    paper = Paper(authors=("  John Doe  ", "Jane Doe  "))

    result = PaperNormalizer().normalize(paper)

    assert result.authors == ("John Doe", "Jane Doe")


def test_normalizer_normalizes_doi():
    paper = Paper(doi=" https://doi.org/10.1234/TEST ")

    result = PaperNormalizer().normalize(paper)

    assert result.doi == "10.1234/TEST"


def test_normalizer_normalizes_pmid():
    paper = Paper(pmid=" PMID: 123456 ")

    result = PaperNormalizer().normalize(paper)

    assert result.pmid == "123456"


def test_normalizer_does_not_mutate_original():
    paper = Paper(title="  Original   Title  ")

    result = PaperNormalizer().normalize(paper)

    assert paper.title == "  Original   Title  "
    assert result.title == "Original Title"


def test_normalizer_preserves_provenance():
    item = provenance()
    result = PaperNormalizer().normalize(Paper(title="  Memory  ", provenances=(item,)))

    assert result.provenances == (item,)
