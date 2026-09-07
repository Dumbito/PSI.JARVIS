from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone

from psi_jarvis.application.acquisition.contracts import AcquisitionResult, BibliographicQuery
from psi_jarvis.domain.bibliography.provenance import AcquisitionReceipt


DEFAULT_MAX_REMOTE_RESPONSE_BYTES = 128 * 1024 * 1024


def read_remote_response(response: object, *, max_bytes: int = DEFAULT_MAX_REMOTE_RESPONSE_BYTES) -> bytes:
    """Lee una respuesta HTTP con un límite explícito de memoria."""

    if max_bytes < 1:
        raise ValueError("Remote response size limit must be positive")

    headers = getattr(response, "headers", None)
    if headers is not None:
        content_length = headers.get("Content-Length")
        if content_length is not None:
            try:
                declared_length = int(content_length)
            except (TypeError, ValueError) as exc:
                raise RuntimeError("Invalid HTTP Content-Length header") from exc
            if declared_length > max_bytes:
                raise RuntimeError(
                    f"Remote response exceeds the {max_bytes} byte safety limit"
                )

    try:
        content = response.read(max_bytes + 1)
    except TypeError as exc:
        raise RuntimeError("HTTP response object must support bounded reads") from exc

    if len(content) > max_bytes:
        raise RuntimeError(f"Remote response exceeds the {max_bytes} byte safety limit")
    return content


@dataclass(frozen=True)
class RemoteAcquisitionResponse:
    """Respuesta cruda de un proveedor bibliográfico remoto."""

    raw_content: str
    source_locator: str | None = None


class RemoteBibliographicAdapter(ABC):
    """Base para adaptadores bibliográficos remotos sin lógica de proveedor."""

    source_key: str
    adapter_key: str
    adapter_version: str
    format_name: str
    format_version: str
    mapping_version: str

    def __init__(self, clock=None) -> None:
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def acquire(self, query: BibliographicQuery) -> AcquisitionResult:
        response = self.fetch(query)
        receipt = AcquisitionReceipt.create(
            source_key=self.source_key,
            adapter_key=self.adapter_key,
            adapter_version=self.adapter_version,
            acquired_at=self._clock(),
            request_payload=query.payload(),
            input_content=response.raw_content,
            source_locator=response.source_locator,
        )
        return self.map_response(response, receipt)

    @abstractmethod
    def fetch(self, query: BibliographicQuery):
        """Obtiene una respuesta externa sin convertirla todavía a Paper."""
        raise NotImplementedError

    @abstractmethod
    def map_response(self, response, receipt: AcquisitionReceipt) -> AcquisitionResult:
        """Convierte la respuesta del proveedor en el contrato de adquisición."""
        raise NotImplementedError
