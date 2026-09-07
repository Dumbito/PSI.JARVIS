from dataclasses import dataclass

from psi_jarvis.application.acquisition.contracts import BibliographicQuery
from psi_jarvis.application.acquisition.service import AcquisitionService
from psi_jarvis.application.synchronization.contracts import ExternalSynchronizationResult
from psi_jarvis.application.synchronization.service import BibliographicSynchronizationService


@dataclass(frozen=True)
class ExternalBibliographicSynchronizationService:
    """Orquesta adquisición remota y aplicación de cambios locales controlados."""

    acquisition_service: AcquisitionService
    synchronization_service: BibliographicSynchronizationService

    def synchronize(self, source_key: str, query: BibliographicQuery) -> ExternalSynchronizationResult:
        acquisition = self.acquisition_service.execute_query_from_source(source_key, query)
        if not acquisition.success:
            return ExternalSynchronizationResult(acquisition=acquisition)

        synchronization = self.synchronization_service.synchronize(acquisition.papers)
        return ExternalSynchronizationResult(
            acquisition=acquisition,
            synchronization=synchronization,
        )
