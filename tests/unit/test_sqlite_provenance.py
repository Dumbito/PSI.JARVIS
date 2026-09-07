import sqlite3
from dataclasses import replace
from datetime import datetime, timezone

from psi_jarvis.domain.bibliography import AcquisitionReceipt, BibliographicProvenance
from psi_jarvis.domain.bibliography.provenance import sha256_text
from psi_jarvis.domain.corpus import Corpus
from psi_jarvis.domain.paper import Paper
from psi_jarvis.infrastructure.sqlite_corpus_repository import SQLiteCorpusRepository
from psi_jarvis.infrastructure.sqlite_paper_repository import SQLitePaperRepository


def make_provenance(source_key: str, ordinal: int = 1) -> BibliographicProvenance:
    receipt = AcquisitionReceipt.create(
        source_key=source_key,
        adapter_key="fixture-adapter",
        adapter_version="1",
        acquired_at=datetime(2026, 9, 5, 12, ordinal, tzinfo=timezone.utc),
        request_payload={"location": f"{source_key}.fixture", "context": "test"},
        input_content=f"input-{source_key}-{ordinal}",
        source_locator=f"{source_key}.fixture",
    )
    return BibliographicProvenance(
        receipt=receipt,
        record_ordinal=ordinal,
        format_name="fixture",
        format_version="1",
        mapping_version="1",
        raw_record_sha256=sha256_text(f"record-{source_key}-{ordinal}"),
    )


def test_sqlite_persists_single_and_multiple_provenances_after_reopen(tmp_path):
    database = tmp_path / "provenance.db"
    first = make_provenance("ris")
    second = make_provenance("csv", 2)
    paper = Paper(title="Memory", provenances=(first, second))

    SQLitePaperRepository(database).save(paper)
    reloaded = SQLitePaperRepository(database).get(paper.id)

    assert reloaded is not None
    assert set(reloaded.provenances) == {first, second}
    assert len(reloaded.provenances) == 2


def test_sqlite_upsert_keeps_existing_provenance_when_paper_is_updated(tmp_path):
    database = tmp_path / "upsert.db"
    provenance = make_provenance("ris")
    paper = Paper(title="Original title", provenances=(provenance,))
    repository = SQLitePaperRepository(database)
    repository.save(paper)

    repository.save(replace(paper, title="Updated title", provenances=()))
    loaded = repository.get(paper.id)

    assert loaded is not None
    assert loaded.title == "Updated title"
    assert loaded.provenances == (provenance,)


def test_sqlite_corpus_uses_shared_paper_rehydration_with_provenance(tmp_path):
    database = tmp_path / "corpus.db"
    paper = Paper(title="Memory", provenances=(make_provenance("ris"),))
    paper_repository = SQLitePaperRepository(database)
    paper_repository.save(paper)
    corpus = Corpus.create(__import__("uuid").uuid4(), (paper,))
    corpus_repository = SQLiteCorpusRepository(database)
    corpus_repository.save(corpus)

    loaded = SQLiteCorpusRepository(database).get(corpus.corpus_id)

    assert loaded is not None
    assert loaded.papers[0].provenances == paper.provenances


def test_schema_version_five_migrates_without_inventing_historical_provenance(tmp_path):
    database = tmp_path / "legacy-v5.db"
    connection = sqlite3.connect(database)
    connection.execute("CREATE TABLE schema_version (version INTEGER NOT NULL)")
    connection.execute("INSERT INTO schema_version (version) VALUES (5)")
    connection.execute(
        """
        CREATE TABLE papers (
            paper_id TEXT PRIMARY KEY, title TEXT NOT NULL, authors TEXT NOT NULL,
            abstract TEXT, doi TEXT, pmid TEXT, publication_year INTEGER, journal TEXT
        )
        """
    )
    paper = Paper(title="Historical paper")
    connection.execute(
        "INSERT INTO papers VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (str(paper.id), paper.title, "[]", None, None, None, None, None),
    )
    connection.commit()
    connection.close()

    repository = SQLitePaperRepository(database)
    loaded = repository.get(paper.id)

    assert loaded is not None
    assert loaded.provenances == ()
    with sqlite3.connect(database) as migrated:
        assert migrated.execute("SELECT version FROM schema_version").fetchone()[0] == 7
        assert migrated.execute("SELECT COUNT(*) FROM acquisition_batches").fetchone()[0] == 0
        assert migrated.execute("SELECT COUNT(*) FROM metadata_change_history").fetchone()[0] == 0
