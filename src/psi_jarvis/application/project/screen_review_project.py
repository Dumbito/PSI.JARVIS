from dataclasses import dataclass
from uuid import UUID

from psi_jarvis.application.pipeline.pipeline import PaperPipeline, PipelineResult
from psi_jarvis.domain.paper import Paper
from psi_jarvis.domain.project_repository import ProjectRepository


@dataclass(frozen=True)
class ScreenReviewProjectService:
    """Ejecuta el cribado de un proyecto de revisión existente."""

    project_repository: ProjectRepository
    pipeline: PaperPipeline

    def execute(
        self,
        project_id: UUID,
        papers: list[Paper] | tuple[Paper, ...],
    ) -> PipelineResult:
        project = self.project_repository.get(project_id)
        if project is None:
            raise ValueError(f"Review project not found: {project_id}")

        return self.pipeline.process(
            papers=papers,
            criteria=project.criteria,
            project_id=project.project_id,
        )
