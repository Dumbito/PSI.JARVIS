from dataclasses import dataclass, replace
from datetime import datetime, timezone
import json
from typing import Callable, Protocol

from psi_jarvis.application.synchronization.contracts import (
    MetadataChange,
    SyncConflict,
    SynchronizationResult,
)
from psi_jarvis.domain.paper import Paper
from psi_jarvis.domain.paper_repository import PaperRepository


class MetadataHistoryRepository(Protocol):
    """Puerto para conservar cambios de metadata sin mezclar decisiones de screening."""

    def record(self, change: MetadataChange) -> None: ...


@dataclass(frozen=True)
class BibliographicSynchronizationService:
    """Sincroniza metadata externa de forma conservadora y auditable.

    La sincronización nunca altera resultados ni auditorías de screening. Solo puede
    completar campos locales vacíos; las discrepancias entre valores no vacíos se
    registran como conflictos y se dejan sin resolver automáticamente.
    """

    repository: PaperRepository
    history_repository: MetadataHistoryRepository
    clock: Callable[[], datetime] | None = None

    def synchronize(self, incoming: tuple[Paper, ...] | list[Paper]) -> SynchronizationResult:
        now = (self.clock or (lambda: datetime.now(timezone.utc)))()
        if now.tzinfo is None or now.utcoffset() != timezone.utc.utcoffset(now):
            raise ValueError("Synchronization timestamp must be UTC")
        now = now.astimezone(timezone.utc)

        existing = self.repository.list_all()
        by_identity = self._index(existing)
        new_records = 0
        enriched_records = 0
        unchanged_records = 0
        provenance_only_records = 0
        conflicts: list[SyncConflict] = []
        metadata_changes: list[MetadataChange] = []

        for candidate in incoming:
            identity = self._identity_key(candidate)
            current = by_identity.get(identity)

            if current is None:
                self.repository.save(candidate)
                by_identity[identity] = candidate
                new_records += 1
                continue

            merged_provenances = self._merge_provenances(current, candidate)
            updated, fields, field_conflicts = self._merge_metadata(current, candidate)
            conflicts.extend(field_conflicts)

            if fields:
                batch_id = self._batch_id(candidate)
                source_key, source_record_id = self._provenance_identity(candidate)
                before_json = self._metadata_json(current)
                after_json = self._metadata_json(updated)
                change = MetadataChange(
                    paper_id=current.id,
                    batch_id=batch_id,
                    source_key=source_key,
                    source_record_id=source_record_id,
                    changed_at=now,
                    changed_fields=tuple(fields),
                    before_json=before_json,
                    after_json=after_json,
                )
                self.history_repository.record(change)
                updated = replace(updated, provenances=merged_provenances)
                self.repository.save(updated)
                by_identity[identity] = updated
                metadata_changes.append(change)
                enriched_records += 1
            elif merged_provenances != current.provenances:
                updated = replace(current, provenances=merged_provenances)
                self.repository.save(updated)
                by_identity[identity] = updated
                provenance_only_records += 1
            else:
                unchanged_records += 1

        return SynchronizationResult(
            new_records=new_records,
            enriched_records=enriched_records,
            unchanged_records=unchanged_records,
            provenance_only_records=provenance_only_records,
            conflicts=tuple(conflicts),
            metadata_changes=tuple(metadata_changes),
        )

    @staticmethod
    def _index(papers: tuple[Paper, ...]) -> dict[str, Paper]:
        index: dict[str, Paper] = {}
        for paper in papers:
            key = BibliographicSynchronizationService._identity_key(paper)
            if key in index and index[key].id != paper.id:
                raise ValueError(f"Ambiguous existing paper identity: {key}")
            index[key] = paper
        return index

    @staticmethod
    def _identity_key(paper: Paper) -> str:
        if paper.doi:
            return f"doi:{paper.doi.strip().lower()}"
        if paper.pmid:
            return f"pmid:{paper.pmid.strip()}"
        return f"title:{' '.join(paper.title.lower().split())}"

    @staticmethod
    def _merge_provenances(current: Paper, incoming: Paper):
        by_key = {item.key: item for item in (*current.provenances, *incoming.provenances)}
        return tuple(by_key[key] for key in sorted(by_key))

    @staticmethod
    def _batch_id(paper: Paper):
        if not paper.provenances:
            raise ValueError("Incoming synchronized paper must contain provenance")
        return paper.provenances[0].receipt.batch_id

    @staticmethod
    def _provenance_identity(paper: Paper) -> tuple[str, str | None]:
        if not paper.provenances:
            raise ValueError("Incoming synchronized paper must contain provenance")
        provenance = paper.provenances[0]
        return provenance.source_key, provenance.source_record_id

    @classmethod
    def _merge_metadata(
        cls,
        current: Paper,
        incoming: Paper,
    ) -> tuple[Paper, list[str], list[SyncConflict]]:
        values = {
            "title": current.title,
            "authors": current.authors,
            "abstract": current.abstract,
            "doi": current.doi,
            "pmid": current.pmid,
            "publication_year": current.publication_year,
            "journal": current.journal,
        }
        incoming_values = {
            "title": incoming.title,
            "authors": incoming.authors,
            "abstract": incoming.abstract,
            "doi": incoming.doi,
            "pmid": incoming.pmid,
            "publication_year": incoming.publication_year,
            "journal": incoming.journal,
        }
        changed: list[str] = []
        conflicts: list[SyncConflict] = []
        source_key, source_record_id = cls._provenance_identity(incoming)

        for field, current_value in values.items():
            incoming_value = incoming_values[field]
            if cls._is_empty(current_value) and not cls._is_empty(incoming_value):
                values[field] = incoming_value
                changed.append(field)
            elif (
                not cls._is_empty(current_value)
                and not cls._is_empty(incoming_value)
                and not cls._same_value(field, current_value, incoming_value)
            ):
                conflicts.append(
                    SyncConflict(
                        paper_id=current.id,
                        source_key=source_key,
                        source_record_id=source_record_id,
                        field=field,
                        existing_value=current_value,
                        incoming_value=incoming_value,
                    )
                )

        return replace(current, **values), changed, conflicts

    @staticmethod
    def _is_empty(value: object) -> bool:
        return value is None or value == "" or value == ()

    @staticmethod
    def _same_value(field: str, left: object, right: object) -> bool:
        if field == "title" and isinstance(left, str) and isinstance(right, str):
            return " ".join(left.lower().split()) == " ".join(right.lower().split())
        return left == right

    @staticmethod
    def _metadata_json(paper: Paper) -> str:
        return json.dumps(
            {
                "abstract": paper.abstract,
                "authors": list(paper.authors),
                "doi": paper.doi,
                "journal": paper.journal,
                "pmid": paper.pmid,
                "publication_year": paper.publication_year,
                "title": paper.title,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
