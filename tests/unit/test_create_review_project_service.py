import pytest

from psi_jarvis.application.project.create_review_project import CreateReviewProjectService
from psi_jarvis.domain.criteria.screening import ScreeningCriteria
from psi_jarvis.domain.project import ReviewProject


class InMemoryProjectRepository:
    def __init__(self) -> None:
        self.projects: dict = {}

    def save(self, project: ReviewProject) -> None:
        self.projects[project.project_id] = project

    def get(self, project_id):
        return self.projects.get(project_id)

    def list_all(self):
        return tuple(self.projects.values())


def make_criteria() -> ScreeningCriteria:
    return ScreeningCriteria(
        topic="cognitive neuroscience",
        inclusion=("human participants",),
        exclusion=("animal studies",),
    )


def test_service_creates_and_persists_project():
    repository = InMemoryProjectRepository()
    service = CreateReviewProjectService(repository)

    project = service.execute(
        name="Memory Review",
        research_question="How is memory related to intelligence?",
        criteria=make_criteria(),
    )

    assert project.name == "Memory Review"
    assert repository.get(project.project_id) == project


def test_service_normalizes_project_data_before_persisting():
    repository = InMemoryProjectRepository()
    service = CreateReviewProjectService(repository)

    project = service.execute(
        name="  Memory Review  ",
        research_question="  How is memory related to intelligence?  ",
        criteria=make_criteria(),
    )

    assert project.name == "Memory Review"
    assert project.research_question == "How is memory related to intelligence?"
    assert repository.get(project.project_id) == project


def test_service_rejects_empty_project_name():
    repository = InMemoryProjectRepository()
    service = CreateReviewProjectService(repository)

    with pytest.raises(ValueError, match="name cannot be empty"):
        service.execute(name="   ", criteria=make_criteria())


def test_service_rejects_invalid_criteria():
    repository = InMemoryProjectRepository()
    service = CreateReviewProjectService(repository)

    with pytest.raises(ValueError, match="topic cannot be empty"):
        service.execute(
            name="Memory Review",
            criteria=ScreeningCriteria(topic="   "),
        )
