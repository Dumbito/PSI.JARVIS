from typing import Protocol

from uuid import UUID

from psi_jarvis.domain.project import ReviewProject


class ProjectRepository(Protocol):
    """Contrato para persistir y recuperar proyectos de revisión."""

    def save(self, project: ReviewProject) -> None: ...

    def get(self, project_id: UUID) -> ReviewProject | None: ...

    def list_all(self) -> tuple[ReviewProject, ...]: ...
