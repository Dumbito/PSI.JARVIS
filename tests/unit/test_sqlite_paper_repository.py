from psi_jarvis.domain.paper import Paper
from psi_jarvis.infrastructure.sqlite_paper_repository import SQLitePaperRepository


def test_sqlite_paper_repository_persists_and_retrieves(tmp_path):
    repository = SQLitePaperRepository(tmp_path / "jarvis.db")
    paper = Paper(
        title="Memory and Intelligence in Adults",
        authors=("John Doe", "Jane Doe"),
        abstract="Study of memory and intelligence.",
        doi="10.1234/example.doi",
        pmid="12345678",
        publication_year=2026,
        journal="Journal of Cognitive Neuroscience",
    )

    repository.save(paper)
    loaded = repository.get(paper.id)

    assert loaded == paper
    assert loaded is not None
    assert loaded.id == paper.id
    assert loaded.authors == ("John Doe", "Jane Doe")


def test_sqlite_paper_repository_returns_none_for_unknown_id(tmp_path):
    repository = SQLitePaperRepository(tmp_path / "jarvis.db")

    assert repository.get(__import__("uuid").uuid4()) is None


def test_sqlite_paper_repository_lists_all(tmp_path):
    repository = SQLitePaperRepository(tmp_path / "jarvis.db")
    paper_a = Paper(title="Paper A")
    paper_b = Paper(title="Paper B")

    repository.save(paper_a)
    repository.save(paper_b)

    assert repository.list_all() == (paper_a, paper_b)


def test_sqlite_paper_repository_delete_removes_paper_and_provenance(tmp_path):
    from datetime import datetime, timezone
    import sqlite3

    from psi_jarvis.domain.bibliography.provenance import BibliographicProvenance, AcquisitionReceipt
    from psi_jarvis.domain.bibliography.provenance import sha256_text

    repository = SQLitePaperRepository(tmp_path / "jarvis.db")
    receipt = AcquisitionReceipt.create(
        source_key="ris",
        adapter_key="local-ris",
        adapter_version="1",
        acquired_at=datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc),
        request_payload={"location": "fixture.ris"},
        input_content="TY  - JOUR",
        source_locator="fixture.ris",
    )
    paper = Paper(
        title="Deletable paper",
        provenances=(
            BibliographicProvenance(
                receipt=receipt,
                record_ordinal=1,
                format_name="RIS",
                format_version="1",
                mapping_version="1",
                raw_record_sha256=sha256_text("raw-record"),
            ),
        ),
    )

    repository.save(paper)

    repository.delete(paper.id)

    assert repository.get(paper.id) is None
    assert repository.list_all() == ()

    with sqlite3.connect(tmp_path / "jarvis.db") as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM paper_provenances WHERE paper_id = ?",
            (str(paper.id),),
        ).fetchone()[0] == 0
