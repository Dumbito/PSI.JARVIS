from dataclasses import dataclass
from datetime import datetime, UTC
from uuid import UUID
import json

from psi_jarvis.application.acquisition.contracts import AcquisitionResult
from psi_jarvis.domain.bibliography.provenance import sha256_text


@dataclass(frozen=True)
class MetadataChange:
    """Cambio controlado de metadata detectado durante una sincronización."""

    paper_id: UUID
    batch_id: UUID
    source_key: str
    source_record_id: str | None
    changed_at: datetime
    changed_fields: tuple[str, ...]
    before_json: str
    after_json: str

    def __post_init__(self) -> None:
        if (
            self.changed_at.tzinfo is None
            or self.changed_at.utcoffset() != UTC.utcoffset(self.changed_at)
        ):
            raise ValueError("Metadata change timestamp must be UTC")
        if not self.changed_fields:
            raise ValueError("Metadata change must contain at least one changed field")
        if self.source_key.strip() == "":
            raise ValueError("Metadata change source key cannot be empty")
        for payload_name, payload in (
            ("before", self.before_json),
            ("after", self.after_json),
        ):
            try:
                decoded = json.loads(payload)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Metadata change {payload_name} json is invalid"
                ) from exc
            if not isinstance(decoded, dict):
                raise ValueError(
                    f"Metadata change {payload_name} json must be an object"
                )

    @property
    def key(self) -> str:
        return sha256_text(
            "|".join(
                (
                    str(self.paper_id),
                    str(self.batch_id),
                    self.source_key,
                    self.source_record_id or "",
                    ",".join(self.changed_fields),
                    self.before_json,
                    self.after_json,
                )
            )
        )


@dataclass(frozen=True)
class SyncConflict:
    """Conflicto de metadata que no se aplica automáticamente."""

    paper_id: UUID
    source_key: str
    source_record_id: str | None
    field: str
    existing_value: object
    incoming_value: object


@dataclass(frozen=True)
class SynchronizationResult:
    """Resultado auditable de una sincronización externa."""

    new_records: int = 0
    enriched_records: int = 0
    unchanged_records: int = 0
    provenance_only_records: int = 0
    conflicts: tuple[SyncConflict, ...] = ()
    metadata_changes: tuple[MetadataChange, ...] = ()

    @property
    def conflict_count(self) -> int:
        return len(self.conflicts)

    @property
    def success(self) -> bool:
        return self.conflict_count == 0


@dataclass(frozen=True)
class ExternalSynchronizationResult:
    """Resultado combinado de adquisición remota y sincronización local."""

    acquisition: AcquisitionResult
    synchronization: SynchronizationResult | None = None

    @property
    def success(self) -> bool:
        if not self.acquisition.success:
            return False
        return self.synchronization is None or self.synchronization.success
