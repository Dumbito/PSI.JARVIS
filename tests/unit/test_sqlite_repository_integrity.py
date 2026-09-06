import sqlite3
from pathlib import Path

from psi_jarvis.domain.paper import Paper
from psi_jarvis.infrastructure.paper_repository import InMemoryPaperRepository
from psi_jarvis.infrastructure.sqlite_corpus_repository import SQLiteCorpusRepository
from psi_jarvis.infrastructure.sqlite_paper_repository import SQLitePaperRepository
from psi_jarvis.infrastructure.sqlite_project_repository import SQLiteProjectRepository
from psi_jarvis.infrastructure.sqlite_screening_audit_repository import SQLiteScreeningAuditRepository
from psi_jarvis.infrastructure.sqlite_screening_execution_repository import SQLiteScreeningExecutionRepository
from psi_jarvis.infrastructure.sqlite_screening_result_repository import SQLiteScreeningResultRepository
from psi_jarvis.infrastructure.sqlite_screening_run_repository import SQLiteScreeningRunRepository


SQLITE_SOURCES = (
    Path("src/psi_jarvis/infrastructure/sqlite_corpus_repository.py"),
    Path("src/psi_jarvis/infrastructure/sqlite_project_repository.py"),
    Path("src/psi_jarvis/infrastructure/sqlite_screening_audit_repository.py"),
    Path("src/psi_jarvis/infrastructure/sqlite_screening_execution_repository.py"),
    Path("src/psi_jarvis/infrastructure/sqlite_screening_result_repository.py"),
    Path("src/psi_jarvis/infrastructure/sqlite_screening_run_repository.py"),
    Path("src/psi_jarvis/infrastructure/sqlite_screening_persistence.py"),
)


def test_sqlite_persistence_does_not_use_destructive_replace():
    violations = [
        str(path)
        for path in SQLITE_SOURCES
        if "INSERT OR REPLACE" in path.read_text()
    ]
    assert violations == []


def test_sqlite_repository_connections_enable_foreign_keys(tmp_path):
    factories = (
        SQLiteCorpusRepository,
        SQLiteProjectRepository,
        SQLiteScreeningAuditRepository,
        SQLiteScreeningExecutionRepository,
        SQLiteScreeningResultRepository,
        SQLiteScreeningRunRepository,
    )

    for factory in factories:
        repository = factory(tmp_path / f"{factory.__name__}.db")
        with repository._connect() as connection:
            assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1


def test_in_memory_paper_repository_delete_is_idempotent():
    repository = InMemoryPaperRepository()
    paper = Paper(title="Delete")
    repository.save(paper)

    repository.delete(paper.id)
    repository.delete(paper.id)

    assert repository.get(paper.id) is None
    assert repository.list_all() == ()


def test_sqlite_paper_delete_leaves_related_rows_clean(tmp_path):
    database = tmp_path / "papers.db"
    repository = SQLitePaperRepository(database)
    paper = Paper(title="Delete integrity")

    repository.save(paper)
    repository.delete(paper.id)

    with sqlite3.connect(database) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM papers WHERE paper_id = ?",
            (str(paper.id),),
        ).fetchone()[0] == 0
        assert connection.execute(
            "SELECT COUNT(*) FROM corpus_papers WHERE paper_id = ?",
            (str(paper.id),),
        ).fetchone()[0] == 0
        assert connection.execute(
            "SELECT COUNT(*) FROM paper_provenances WHERE paper_id = ?",
            (str(paper.id),),
        ).fetchone()[0] == 0


def test_sqlite_paper_delete_is_idempotent(tmp_path):
    repository = SQLitePaperRepository(tmp_path / "papers.db")
    paper = Paper(title="Delete twice")

    repository.save(paper)
    repository.delete(paper.id)
    repository.delete(paper.id)

    assert repository.get(paper.id) is None


def test_expected_upsert_conflicts_exist():
    expected = {
        "src/psi_jarvis/infrastructure/sqlite_project_repository.py":
            "ON CONFLICT(project_id) DO UPDATE",
        "src/psi_jarvis/infrastructure/sqlite_corpus_repository.py":
            "ON CONFLICT(corpus_id) DO UPDATE",
        "src/psi_jarvis/infrastructure/sqlite_screening_run_repository.py":
            "ON CONFLICT(run_id) DO UPDATE",
        "src/psi_jarvis/infrastructure/sqlite_screening_result_repository.py":
            "ON CONFLICT(result_key) DO UPDATE",
        "src/psi_jarvis/infrastructure/sqlite_screening_audit_repository.py":
            "ON CONFLICT(audit_key) DO UPDATE",
        "src/psi_jarvis/infrastructure/sqlite_screening_persistence.py":
            "ON CONFLICT(run_id) DO UPDATE",
    }

    for filename, fragment in expected.items():
        assert fragment in Path(filename).read_text(), filename


def test_screening_execution_marker_is_idempotent():
    source = Path(
        "src/psi_jarvis/infrastructure/sqlite_screening_execution_repository.py"
    ).read_text()

    assert "INSERT INTO screening_executions" in source
    assert "ON CONFLICT(run_id) DO NOTHING" in source
