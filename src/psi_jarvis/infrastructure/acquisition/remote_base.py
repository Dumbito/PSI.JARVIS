from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone

from psi_jarvis.application.acquisition.contracts import AcquisitionResult, BibliographicQuery
from psi_jarvis.domain.bibliography.provenance import AcquisitionReceipt


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
