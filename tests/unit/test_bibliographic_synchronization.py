from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

import pytest

from psi_jarvis.application.synchronization import BibliographicSynchronizationService
from psi_jarvis.application.synchronization.contracts import MetadataChange
from psi_jarvis.domain.bibliography.provenance import AcquisitionReceipt, BibliographicProvenance, sha256_text
from psi_jarvis.domain.paper import Paper
from psi_jarvis.infrastructure.sqlite_metadata_history_repository import SQLiteMetadataHistoryRepository


FIXED_TIME = datetime(2026, 9, 7, 4, 40, tzinfo=timezone.utc)


@dataclass
class MemoryPaperRepository:
    papers: list[Paper]

    def save(self, paper: Paper) -> None:
        for index, current in enumerate(self.papers):
            if current.id == paper.id:
                self.papers[index] = paper
                return
        self.papers.append(paper)

    def get(self, paper_id: UUID) -> Paper | None:
        return next((paper for paper in self.papers if paper.id == paper_id), None)

    def list_all(self) -> tuple[Paper, ...]:
        return tuple(self.papers)

    def delete(self, paper_id: UUID) -> None:
        self.papers[:] = [paper for paper in self.papers if paper.id != paper_id]


@dataclass
class MemoryHistoryRepository:
    changes: list[MetadataChange]

    def record(self, change: MetadataChange) -> None:
        self.changes.append(change)


def provenance(source_key="pubmed", source_record_id="123"):
    receipt = AcquisitionReceipt.create(
        source_key=source_key,
        adapter_key=f"{source_key}-test",
        adapter_version="1",
        acquired_at=FIXED_TIME,
        request_payload={"q": "memory"},
        input_content=f"{source_key}:{source_record_id}",
    )
    return BibliographicProvenance(
        receipt=receipt,
        record_ordinal=1,
        format_name="test",
        format_version="1",
        mapping_version="1",
        raw_record_sha256=sha256_text(f"{source_key}:{source_record_id}"),
        source_record_id=source_record_id,
    )


def test_sync_adds_new_external_record_with_provenance():
    repository = MemoryPaperRepository([])
    history = MemoryHistoryRepository([])
    incoming = Paper(title="New paper", doi="10.1000/new", provenances=(provenance(),))

    result = BibliographicSynchronizationService(repository, history, lambda: FIXED_TIME).synchronize((incoming,))

    assert result.new_records == 1
    assert repository.list_all() == (incoming,)
    assert history.changes == []


def test_sync_enriches_only_empty_metadata_and_records_history():
    current = Paper(title="Memory", doi="10.1000/memory", abstract=None, journal=None, authors=())
    incoming = Paper(
        id=current.id,
        title="Memory",
        doi="10.1000/memory",
        abstract="A useful abstract",
        journal="Journal of Memory",
        authors=("A. Author",),
        provenances=(provenance(),),
    )
    repository = MemoryPaperRepository([current])
    history = MemoryHistoryRepository([])

    result = BibliographicSynchronizationService(repository, history, lambda: FIXED_TIME).synchronize((incoming,))

    updated = repository.get(current.id)
    assert result.enriched_records == 1
    assert result.conflict_count == 0
    assert updated is not None
    assert updated.abstract == "A useful abstract"
    assert updated.journal == "Journal of Memory"
    assert updated.authors == ("A. Author",)
    assert updated.provenances == incoming.provenances
    assert history.changes[0].changed_fields == ("authors", "abstract", "journal")
    assert history.changes[0].paper_id == current.id


def test_sync_preserves_existing_metadata_and_reports_conflicts():
    current = Paper(
        title="Memory",
        doi="10.1000/memory",
        abstract="Existing abstract",
        journal="Existing journal",
        authors=("Existing Author",),
    )
    incoming = Paper(
        id=current.id,
        title="Memory",
        doi="10.1000/memory",
        abstract="Conflicting abstract",
        journal="Incoming journal",
        authors=("Incoming Author",),
        provenances=(provenance(source_record_id="456"),),
    )
    repository = MemoryPaperRepository([current])
    history = MemoryHistoryRepository([])

    result = BibliographicSynchronizationService(repository, history, lambda: FIXED_TIME).synchronize((incoming,))

    updated = repository.get(current.id)
    assert result.enriched_records == 0
    assert {conflict.field for conflict in result.conflicts} == {"authors", "abstract", "journal"}
    assert updated is not None
    assert updated.abstract == "Existing abstract"
    assert updated.journal == "Existing journal"
    assert updated.authors == ("Existing Author",)
    assert len(updated.provenances) == 1
    assert history.changes == []


def test_sync_is_idempotent_and_can_add_new_provenance_without_metadata_change():
    current_provenance = provenance(source_record_id="123")
    incoming_provenance = provenance(source_record_id="456")
    current = Paper(title="Memory", doi="10.1000/memory", provenances=(current_provenance,))
    incoming = Paper(id=current.id, title="Memory", doi="10.1000/memory", provenances=(incoming_provenance,))
    repository = MemoryPaperRepository([current])
    history = MemoryHistoryRepository([])
    service = BibliographicSynchronizationService(repository, history, lambda: FIXED_TIME)

    first = service.synchronize((incoming,))
    second = service.synchronize((incoming,))

    assert first.provenance_only_records == 1
    assert second.unchanged_records == 1
    assert len(repository.get(current.id).provenances) == 2
    assert history.changes == []


def test_sync_requires_provenance_for_external_records():
    service = BibliographicSynchronizationService(
        MemoryPaperRepository([]),
        MemoryHistoryRepository([]),
        lambda: FIXED_TIME,
    )

    with pytest.raises(ValueError, match="must contain provenance"):
        service.synchronize((Paper(title="Untracked"),))


def test_sqlite_metadata_history_round_trip_and_idempotency(tmp_path):
    repository = SQLiteMetadataHistoryRepository(tmp_path / "history.db")
    change = MetadataChange(
        paper_id=UUID("00000000-0000-0000-0000-000000000001"),
        batch_id=UUID("00000000-0000-0000-0000-000000000002"),
        source_key="pubmed",
        source_record_id="123",
        changed_at=FIXED_TIME,
        changed_fields=("abstract",),
        before_json='{"abstract":null}',
        after_json='{"abstract":"A"}',
    )

    repository.record(change)
    repository.record(change)

    assert repository.list_all() == (change,)
