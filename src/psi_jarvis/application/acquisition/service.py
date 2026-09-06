from dataclasses import dataclass

from psi_jarvis.application.acquisition.contracts import (
    AcquisitionRequest,
    AcquisitionResult,
    BibliographicAcquisitionPort,
)


@dataclass(frozen=True)
class AcquisitionService:
    """Orquesta adquisición sin aplicar normalización ni reglas científicas."""

    port: BibliographicAcquisitionPort

    def execute(self, request: AcquisitionRequest) -> AcquisitionResult:
        return self.port.acquire(request)
