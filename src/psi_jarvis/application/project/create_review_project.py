from dataclasses import dataclass

from psi_jarvis.domain.criteria.screening import ScreeningCriteria
from psi_jarvis.domain.project import ReviewProject
from psi_jarvis.domain.project_repository import ProjectRepository


@dataclass(frozen=True)
class CreateReviewProjectService:
    """Crea y persiste proyectos de revisión científica."""

    project_repository: ProjectRepository

    def execute(
        self,
        name: str,
        criteria: ScreeningCriteria,
        research_question: str = "",
    ) -> ReviewProject:
        project = ReviewProject.create(
            name=name,
            criteria=criteria,
            research_question=research_question,
        )
        self.project_repository.save(project)
        return project
