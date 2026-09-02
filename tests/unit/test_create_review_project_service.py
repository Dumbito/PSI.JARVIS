import pytest

from psi_jarvis.application.project.create_review_project import CreateReviewProjectService
from psi_jarvis.domain.criteria.screening import ScreeningCriteria

def test_create_review_project_service_creates_project():
    service = CreateReviewProjectService()
    criteria = ScreeningCriteria(topic="memory")

    project = service.execute(
        name="Memory and Intelligence Review",
        criteria=criteria,
        research_question="What is the relationship between memory and intelligence?",
    )

    assert project.name == "Memory and Intelligence Review"
    assert project.research_question == "What is the relationship between memory and intelligence?"
    assert project.criteria == criteria
    assert project.project_id is not None

def test_create_review_project_service_uses_domain_normalization():
    service = CreateReviewProjectService()
    project = service.execute(
        name="  Memory Review  ",
        criteria=ScreeningCriteria(topic="memory"),
        research_question="  Research question  ",
    )

    assert project.name == "Memory Review"
    assert project.research_question == "Research question"

def test_create_review_project_service_rejects_empty_name():
    service = CreateReviewProjectService()

    with pytest.raises(ValueError, match="project name cannot be empty"):
        service.execute(
            name="   ",
            criteria=ScreeningCriteria(topic="memory"),
        )

def test_create_review_project_service_requires_valid_criteria():
    service = CreateReviewProjectService()

    with pytest.raises(ValueError, match="Screening topic cannot be empty"):
        service.execute(
            name="Memory Review",
            criteria=ScreeningCriteria(topic="   "),
        )
