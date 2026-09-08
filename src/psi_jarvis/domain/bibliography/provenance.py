import json
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from uuid import UUID, uuid5


def canonical_json(payload: object) -> str:
    return json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def sha256_text(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class AcquisitionReceipt:
    """Registro inmutable y reproducible de una adquisición bibliográfica."""

    batch_id: UUID
    source_key: str
    adapter_key: str
    adapter_version: str
    acquired_at: datetime
    request_json: str
    request_sha256: str
    input_sha256: str
    source_locator: str | None = None

    def __post_init__(self) -> None:
        for value, name in (
            (self.source_key, "source key"),
            (self.adapter_key, "adapter key"),
            (self.adapter_version, "adapter version"),
            (self.request_json, "request json"),
        ):
            if not value.strip():
                raise ValueError(f"Acquisition receipt {name} cannot be empty")
        if (
            self.acquired_at.tzinfo is None
            or self.acquired_at.utcoffset() != UTC.utcoffset(self.acquired_at)
        ):
            raise ValueError("Acquisition receipt timestamp must be UTC")
        if self.request_sha256 != sha256_text(self.request_json):
            raise ValueError(
                "Acquisition receipt request hash does not match request json"
            )
        if len(self.input_sha256) != 64:
            raise ValueError("Acquisition receipt input hash must be a SHA-256 digest")

    @classmethod
    def create(
        cls,
        *,
        source_key: str,
        adapter_key: str,
        adapter_version: str,
        acquired_at: datetime,
        request_payload: object,
        input_content: str,
        source_locator: str | None = None,
    ) -> "AcquisitionReceipt":
        request_json = canonical_json(request_payload)
        input_sha256 = sha256_text(input_content)
        timestamp = acquired_at.astimezone(UTC).isoformat()
        batch_id = uuid5(
            UUID("6ba7b811-9dad-11d1-80b4-00c04fd430c8"),
            "|".join(
                (
                    source_key,
                    adapter_key,
                    adapter_version,
                    timestamp,
                    request_json,
                    input_sha256,
                )
            ),
        )
        return cls(
            batch_id=batch_id,
            source_key=source_key,
            adapter_key=adapter_key,
            adapter_version=adapter_version,
            acquired_at=acquired_at.astimezone(UTC),
            request_json=request_json,
            request_sha256=sha256_text(request_json),
            input_sha256=input_sha256,
            source_locator=source_locator,
        )

    def to_json(self) -> str:
        return canonical_json(
            {
                "acquired_at": self.acquired_at.isoformat(),
                "adapter_key": self.adapter_key,
                "adapter_version": self.adapter_version,
                "batch_id": str(self.batch_id),
                "input_sha256": self.input_sha256,
                "request_json": self.request_json,
                "request_sha256": self.request_sha256,
                "source_key": self.source_key,
                "source_locator": self.source_locator,
            }
        )


@dataclass(frozen=True)
class BibliographicProvenance:
    """Procedencia inmutable de un registro bibliográfico dentro de un lote."""

    receipt: AcquisitionReceipt
    record_ordinal: int
    format_name: str
    format_version: str
    mapping_version: str
    raw_record_sha256: str
    source_record_id: str | None = None

    def __post_init__(self) -> None:
        if self.record_ordinal < 1:
            raise ValueError("Bibliographic provenance record ordinal must be positive")
        for value, name in (
            (self.format_name, "format name"),
            (self.format_version, "format version"),
            (self.mapping_version, "mapping version"),
        ):
            if not value.strip():
                raise ValueError(f"Bibliographic provenance {name} cannot be empty")
        if len(self.raw_record_sha256) != 64:
            raise ValueError(
                "Bibliographic provenance raw record hash must be a SHA-256 digest"
            )

    @property
    def source_key(self) -> str:
        return self.receipt.source_key

    @property
    def key(self) -> str:
        return sha256_text(
            "|".join(
                (
                    str(self.receipt.batch_id),
                    str(self.record_ordinal),
                    self.raw_record_sha256,
                )
            )
        )
