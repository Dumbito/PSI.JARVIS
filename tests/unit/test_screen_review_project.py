import pytest
from uuid import uuid4

from psi_jarvis.application.pipeline.pipeline import PaperPipeline
from psi_jarvis.application.project.screen_review_project import ScreenReviewProjectService
from psi_jarvis.domain.criteria.screening import ScreeningCriteria
from psi_jarvis.domain.paper import Paper
from psi_jarvis.domain.project import ReviewProject


class FakeProjectRepository:
    def __init__(self, project):
        self.project = project

    def get(self, project_id):
        if self.project.project_id == project_id:
            return self.project
        return None


def test_screen_review_project_uses_project_criteria(tmp_path):
    project = ReviewProject.create(
        name="Neuropsychology review",
        research_question="Does memory relate to intelligence?",
        criteria=ScreeningCriteria(
            topic="intelligence",
            inclusion=("memory",),
            exclusion=("animal",),
        ),
    )

    repository = FakeProjectRepository(project)
    service = ScreenReviewProjectService(
        project_repository=repository,
        pipeline=PaperPipeline(),
    )

    papers = [
        Paper(
            title="Memory and intelligence in adults",
            abstract="Study of memory and intelligence.",
        ),
    ]

    result = service.execute(project.project_id, papers)

    assert result.run.project_id == project.project_id
    assert result.run.criteria_version
    assert result.screened_papers == 1


def test_screen_review_project_rejects_unknown_project():
    repository = FakeProjectRepository(
        ReviewProject.create(
            name="Existing",
            criteria=ScreeningCriteria(topic="test"),
        )
    )
    service = ScreenReviewProjectService(
        project_repository=repository,
        pipeline=PaperPipeline(),
    )

    with pytest.raises(ValueError, match="Review project not found"):
        service.execute(uuid4(), ())
