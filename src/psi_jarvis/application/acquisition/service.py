from dataclasses import dataclass

from psi_jarvis.application.acquisition.contracts import (
    AcquisitionRequest,
    AcquisitionResult,
    BibliographicAcquisitionPort,
    BibliographicQuery,
    BibliographicSourceResolver,
)


@dataclass(frozen=True)
class AcquisitionService:
    """Orquesta adquisición sin aplicar normalización ni reglas científicas."""

    port: BibliographicAcquisitionPort

    def execute(self, request: AcquisitionRequest) -> AcquisitionResult:
        return self.port.acquire(request)

    def execute_query(self, query: BibliographicQuery) -> AcquisitionResult:
        return self.port.acquire(query)

    def execute_remote_query(
        self,
        source_key: str,
        query: BibliographicQuery,
        resolver: BibliographicSourceResolver,
    ) -> AcquisitionResult:
        """Resuelve una fuente remota mediante un puerto y ejecuta la consulta."""
        adapter = resolver.resolve(source_key)
        return adapter.acquire(query)
