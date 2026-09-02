import pytest

from psi_jarvis.domain.criteria.screening import ScreeningCriteria
from psi_jarvis.domain.project import ReviewProject


def make_project() -> ReviewProject:
    criteria = ScreeningCriteria(
        topic="cognitive neuroscience",
        inclusion=("human participants",),
        exclusion=("animal studies",),
    )
    return ReviewProject.create(
        name="Memory Review",
        research_question="How is memory related to intelligence?",
        criteria=criteria,
    )


def test_sqlite_project_repository_saves_and_gets_project(tmp_path):
    from psi_jarvis.infrastructure.sqlite_project_repository import SQLiteProjectRepository

    repository = SQLiteProjectRepository(tmp_path / "jarvis.db")
    project = make_project()
    repository.save(project)

    loaded = repository.get(project.project_id)

    assert loaded == project


def test_sqlite_project_repository_returns_none_for_unknown_project(tmp_path):
    from uuid import uuid4
    from psi_jarvis.infrastructure.sqlite_project_repository import SQLiteProjectRepository

    repository = SQLiteProjectRepository(tmp_path / "jarvis.db")

    assert repository.get(uuid4()) is None


def test_sqlite_project_repository_lists_projects(tmp_path):
    from psi_jarvis.infrastructure.sqlite_project_repository import SQLiteProjectRepository

    repository = SQLiteProjectRepository(tmp_path / "jarvis.db")
    first = make_project()
    second = make_project()

    repository.save(first)
    repository.save(second)

    projects = repository.list_all()

    assert projects == (first, second)


def test_sqlite_project_repository_overwrites_same_project(tmp_path):
    from dataclasses import replace
    from psi_jarvis.infrastructure.sqlite_project_repository import SQLiteProjectRepository

    repository = SQLiteProjectRepository(tmp_path / "jarvis.db")
    project = make_project()
    updated = replace(project, name="Updated Review")

    repository.save(project)
    repository.save(updated)

    assert repository.get(project.project_id) == updated
    assert repository.list_all() == (updated,)
