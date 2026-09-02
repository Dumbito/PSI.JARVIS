from psi_jarvis.domain.criteria.screening import ScreeningCriteria
from psi_jarvis.domain.project import ReviewProject

def test_create_review_project_generates_identity_and_timestamp():
    criteria = ScreeningCriteria(topic="memory")
    project = ReviewProject.create(name="Memory Review", criteria=criteria, research_question="How is memory related to intelligence?")

    assert project.name == "Memory Review"
    assert project.research_question == "How is memory related to intelligence?"
    assert project.criteria == criteria
    assert project.project_id is not None
    assert project.created_at.tzinfo is not None

def test_create_review_project_strips_text():
    project = ReviewProject.create(name="  Memory Review  ", criteria=ScreeningCriteria(topic="memory"), research_question="  Question  ")

    assert project.name == "Memory Review"
    assert project.research_question == "Question"

def test_create_review_project_rejects_empty_name():
    import pytest
    with pytest.raises(ValueError, match="project name cannot be empty"):
        ReviewProject.create(name="   ", criteria=ScreeningCriteria(topic="memory"))
