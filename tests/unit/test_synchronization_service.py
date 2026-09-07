from datetime import datetime, timezone
from dataclasses import dataclass, field
from uuid import UUID, uuid4

from psi_jarvis.application.synchronization import BibliographicSynchronizationService
from psi_jarvis.application.synchronization.contracts import MetadataChange
from psi_jarvis.domain.bibliography import AcquisitionReceipt, BibliographicProvenance
from psi_jarvis.domain.bibliography.provenance import sha256_text
from psi_jarvis.domain.paper import Paper


@dataclass
class MemoryPaperRepository:
    papers: dict[UUID, Paper] = field(default_factory=dict)

    def save(self, paper: Paper) -> None:
        self.papers[paper.id] = paper

    def get(self, paper_id: UUID):
        return self.papers.get(paper_id)

    def list_all(self):
        return tuple(self.papers.values())

    def delete(self, paper_id: UUID) -> None:
        self.papers.pop(paper_id, None)


@dataclass
class MemoryHistoryRepository:
    changes: list[MetadataChange] = field(default_factory=list)

    def record(self, change: MetadataChange) -> None:
        if change not in self.changes:
            self.changes.append(change)


def provenance(source_key: str, record_id: str, ordinal: int = 1) -> BibliographicProvenance:
    receipt = AcquisitionReceipt.create(
        source_key=source_key,
        adapter_key=f"{source_key}-adapter",
        adapter_version="1",
        acquired_at=datetime(2026, 9, 7, 12, ordinal, tzinfo=timezone.utc),
        request_payload={"q": "memory"},
        input_content=f"{source_key}:{record_id}",
        source_locator=f"{source_key}://{record_id}",
    )
    return BibliographicProvenance(
        receipt=receipt,
        record_ordinal=ordinal,
        format_name=source_key,
        format_version="1",
        mapping_version="1",
        raw_record_sha256=sha256_text(f"record:{source_key}:{record_id}"),
        source_record_id=record_id,
    )


def test_synchronization_detects_new_enriched_unchanged_and_conflicting_records():
    repository = MemoryPaperRepository()
    history = MemoryHistoryRepository()
    service = BibliographicSynchronizationService(
        repository=repository,
        history_repository=history,
        clock=lambda: datetime(2026, 9, 7, 13, tzinfo=timezone.utc),
    )

    new_paper = Paper(
        title="New study",
        abstract="Abstract",
        provenances=(provenance("pubmed", "1001"),),
    )
    assert service.synchronize((new_paper,)).new_records == 1

    existing = Paper(
        id=uuid4(),
        title="Existing study",
        abstract=None,
        doi="10.1000/example",
        provenances=(provenance("pubmed", "2001"),),
    )
    repository.save(existing)

    enriched = Paper(
        id=uuid4(),
        title="Existing study",
        abstract="Recovered abstract",
        doi="10.1000/example",
        provenances=(provenance("scopus", "SCOPUS:2001"),),
    )
    enriched_result = service.synchronize((enriched,))
    loaded = repository.get(existing.id)

    assert enriched_result.enriched_records == 1
    assert loaded is not None
    assert loaded.abstract == "Recovered abstract"
    assert {item.source_key for item in loaded.provenances} == {"pubmed", "scopus"}
    assert len(history.changes) == 1

    unchanged_result = service.synchronize((enriched,))
    assert unchanged_result.enriched_records == 0
    assert unchanged_result.conflict_count == 0
    assert unchanged_result.provenance_only_records == 0

    conflicting = Paper(
        id=uuid4(),
        title="Different title",
        abstract="Different abstract",
        doi="10.1000/example",
        provenances=(provenance("wos", "WOS:2001"),),
    )
    conflict_result = service.synchronize((conflicting,))

    assert conflict_result.success is False
    assert conflict_result.conflict_count == 2
    loaded_after_conflict = repository.get(existing.id)
    assert loaded_after_conflict is not None
    assert loaded_after_conflict.title == "Existing study"
    assert loaded_after_conflict.abstract == "Recovered abstract"
    assert any(item.source_key == "wos" for item in loaded_after_conflict.provenances)


def test_synchronization_requires_incoming_provenance():
    repository = MemoryPaperRepository()
    service = BibliographicSynchronizationService(
        repository=repository,
        history_repository=MemoryHistoryRepository(),
        clock=lambda: datetime(2026, 9, 7, 13, tzinfo=timezone.utc),
    )

    try:
        service.synchronize((Paper(title="No provenance"),))
    except ValueError as exc:
        assert str(exc) == "Incoming synchronized paper must contain provenance"
    else:
        raise AssertionError("Synchronization should reject records without provenance")
