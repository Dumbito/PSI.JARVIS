from datetime import datetime, timezone
import sqlite3

from psi_jarvis.application.synchronization import BibliographicSynchronizationService
from psi_jarvis.domain.bibliography.provenance import AcquisitionReceipt, BibliographicProvenance, sha256_text
from psi_jarvis.domain.paper import Paper
from psi_jarvis.infrastructure.sqlite_metadata_history_repository import SQLiteMetadataHistoryRepository
from psi_jarvis.infrastructure.sqlite_paper_repository import SQLitePaperRepository


FIXED_TIME = datetime(2026, 9, 7, 4, 50, tzinfo=timezone.utc)


def make_provenance() -> BibliographicProvenance:
    raw = "pubmed:999"
    receipt = AcquisitionReceipt.create(
        source_key="pubmed",
        adapter_key="pubmed-efetch",
        adapter_version="1",
        acquired_at=FIXED_TIME,
        request_payload={"text": "memory"},
        input_content=raw,
    )
    return BibliographicProvenance(
        receipt=receipt,
        record_ordinal=1,
        format_name="PubMed XML",
        format_version="1",
        mapping_version="1",
        raw_record_sha256=sha256_text(raw),
        source_record_id="999",
    )


def test_metadata_sync_preserves_historical_screening_records(tmp_path):
    database = tmp_path / "psi.db"
    repository = SQLitePaperRepository(database)
    history = SQLiteMetadataHistoryRepository(database)

    current = Paper(title="Memory", doi="10.1000/memory", abstract=None)
    repository.save(current)

    with sqlite3.connect(database) as connection:
        connection.execute(
            """
            INSERT INTO screening_results (
                result_key, paper_id, included, reason, run_id,
                matched_rules, failed_rules, matched_rule_ids, failed_rule_ids,
                criteria_version, rule_traces
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "result-1", str(current.id), 1, "eligible", "run-1",
                "[]", "[]", "[]", "[]", "criteria-1", "[]",
            ),
        )
        connection.execute(
            """
            INSERT INTO screening_audits (
                audit_key, paper_id, included, reason, run_id,
                matched_rules, failed_rules, matched_rule_ids, failed_rule_ids,
                criteria_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "audit-1", str(current.id), 1, "eligible", "run-1",
                "[]", "[]", "[]", "[]", "criteria-1",
            ),
        )
        connection.commit()

    incoming = Paper(
        id=current.id,
        title="Memory",
        doi="10.1000/memory",
        abstract="New abstract from source",
        provenances=(make_provenance(),),
    )

    result = BibliographicSynchronizationService(
        repository,
        history,
        lambda: FIXED_TIME,
    ).synchronize((incoming,))

    assert result.enriched_records == 1
    assert repository.get(current.id).abstract == "New abstract from source"
    assert len(history.list_all()) == 1

    with sqlite3.connect(database) as connection:
        screening_result = connection.execute(
            "SELECT included, reason, run_id, criteria_version FROM screening_results WHERE result_key = ?",
            ("result-1",),
        ).fetchone()
        screening_audit = connection.execute(
            "SELECT included, reason, run_id, criteria_version FROM screening_audits WHERE audit_key = ?",
            ("audit-1",),
        ).fetchone()

    assert screening_result == (1, "eligible", "run-1", "criteria-1")
    assert screening_audit == (1, "eligible", "run-1", "criteria-1")
