from psi_jarvis.domain.criteria.screening import ScreeningCriteria
from psi_jarvis.domain.project import ReviewProject

class CreateReviewProjectService:
    """Crea proyectos de revisión a partir de una definición científica."""

    def execute(
        self,
        name: str,
        criteria: ScreeningCriteria,
        research_question: str = "",
    ) -> ReviewProject:
        return ReviewProject.create(
            name=name,
            criteria=criteria,
            research_question=research_question,
        )
