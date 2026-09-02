import sqlite3
from uuid import uuid4

from psi_jarvis.domain.screening.run import ScreeningRun
from psi_jarvis.infrastructure.sqlite_screening_run_repository import SQLiteScreeningRunRepository


def test_sqlite_screening_run_repository_persists_project_id(tmp_path):
    repository = SQLiteScreeningRunRepository(tmp_path / "jarvis.db")
    project_id = uuid4()

    run = ScreeningRun.create(
        project_id=project_id,
        criteria_version="criteria-v1",
        total_input=10,
        unique_papers=8,
        duplicates_removed=2,
        screened_papers=8,
    )

    repository.save(run)
    loaded = repository.get(run.run_id)

    assert loaded == run
    assert loaded.project_id == project_id

    connection = sqlite3.connect(tmp_path / "jarvis.db")
    row = connection.execute(
        "SELECT project_id FROM screening_runs WHERE run_id = ?",
        (str(run.run_id),),
    ).fetchone()
    connection.close()

    assert row == (str(project_id),)
