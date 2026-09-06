from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

from psi_jarvis.domain.bibliography.provenance import AcquisitionReceipt
from psi_jarvis.domain.paper import Paper


@dataclass(frozen=True)
class AcquisitionRequest:
    """Solicitud agnóstica para adquirir una fuente bibliográfica local."""

    location: str
    context: str = ""
    acquired_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.location.strip():
            raise ValueError("Acquisition request location cannot be empty")
        if self.acquired_at is not None and (
            self.acquired_at.tzinfo is None
            or self.acquired_at.utcoffset() != timezone.utc.utcoffset(self.acquired_at)
        ):
            raise ValueError("Acquisition request timestamp must be UTC")

    def payload(self) -> dict[str, str]:
        return {"context": self.context, "location": self.location}


@dataclass(frozen=True)
class AcquisitionIssue:
    code: str
    message: str
    severity: str = "error"
    record_ordinal: int | None = None

    def __post_init__(self) -> None:
        if self.severity not in {"warning", "error"}:
            raise ValueError("Acquisition issue severity must be warning or error")
        if not self.code.strip() or not self.message.strip():
            raise ValueError("Acquisition issue code and message cannot be empty")
        if self.record_ordinal is not None and self.record_ordinal < 1:
            raise ValueError("Acquisition issue record ordinal must be positive")


@dataclass(frozen=True)
class AcquisitionResult:
    receipt: AcquisitionReceipt | None
    papers: tuple[Paper, ...] = ()
    issues: tuple[AcquisitionIssue, ...] = ()

    @property
    def success(self) -> bool:
        return not any(issue.severity == "error" for issue in self.issues)


class BibliographicAcquisitionPort(Protocol):
    """Puerto para adaptadores bibliográficos sin dependencia de proveedor."""

    def acquire(self, request: AcquisitionRequest) -> AcquisitionResult: ...
