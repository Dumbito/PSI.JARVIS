from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4

from psi_jarvis.domain.criteria.screening import ScreeningCriteria

@dataclass(frozen=True)
class ReviewProject:
    """Representa un proyecto de revisión científica y su definición inicial."""

    project_id: UUID
    name: str
    research_question: str
    criteria: ScreeningCriteria
    created_at: datetime

    @classmethod
    def create(
        cls,
        name: str,
        criteria: ScreeningCriteria,
        research_question: str = "",
    ) -> "ReviewProject":
        normalized_name = name.strip()
        normalized_question = research_question.strip()

        if not normalized_name:
            raise ValueError("Review project name cannot be empty")

        return cls(
            project_id=uuid4(),
            name=normalized_name,
            research_question=normalized_question,
            criteria=criteria,
            created_at=datetime.now(timezone.utc),
        )
