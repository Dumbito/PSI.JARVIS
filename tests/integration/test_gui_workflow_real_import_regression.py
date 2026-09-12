"""End-to-end regression coverage for the real import -> screen -> export
flow, using the actual file-based GUI workflow rather than in-memory
domain services.

This exists because every bug found in a September 2026 manual testing
session (a hard crash on duplicate-DOI deduplication, clipped table
headers, and raw-float report percentages) went completely unnoticed by
the existing unit and integration suites - none of them drove a real
CSV/RIS file through GuiWorkflowService.import_and_screen with SQLite
persistence the way the actual desktop app does. These tests pin that
real path down so a future regression here fails CI instead of waiting
to be found by hand again.
"""

from pathlib import Path
from uuid import UUID

from psi_jarvis.domain.criteria.screening import ScreeningCriteria
from psi_jarvis.domain.project import ReviewProject
from psi_jarvis.gui.data import GuiDataService
from psi_jarvis.gui.workflow import GuiWorkflowService
from psi_jarvis.infrastructure.sqlite_project_repository import SQLiteProjectRepository

REAL_PAPERS_WITH_DUPLICATE_DOI_CSV = "\n".join(
    [
        "title,authors,abstract,doi,pmid,publication_year,journal",
        (
            "Dermatologist-level classification of skin cancer with deep "
            "neural networks,Esteva A;Thrun S,A deep learning convolutional "
            "neural network for artificial intelligence skin lesion "
            "classification.,10.1038/nature21056,,2017,Nature"
        ),
        (
            "Dermatologist-level classification of skin cancer with deep "
            "neural networks,Esteva A;Thrun S,A deep learning convolutional "
            "neural network for artificial intelligence skin lesion "
            "classification.,10.1038/nature21056,,2017,Nature"
        ),
        (
            "Cognitive load and classroom seating,Martinez L,A classroom "
            "study of seating arrangement unrelated to computing.,"
            "10.1234/edu.2015,,2015,Journal of Educational Psychology"
        ),
    ]
)


def _new_project(database_path: Path) -> ReviewProject:
    criteria = ScreeningCriteria(
        topic="artificial intelligence", inclusion=("artificial intelligence",)
    )
    project = ReviewProject.create(
        "Regression Review",
        criteria,
        "Does the real import pipeline still work end to end?",
    )
    SQLiteProjectRepository(database_path).save(project)
    return project


def test_importing_a_duplicate_doi_does_not_crash_and_dedupes_correctly(
    tmp_path: Path,
):
    """Pins the fix for a real crash: importing two CSV rows describing
    the same paper (same DOI) used to raise an uncaught
    sqlite3.IntegrityError on paper_provenances.provenance_key when the
    deduplicator merged their provenance onto the surviving paper.
    """
    database_path = tmp_path / "psi.db"
    csv_path = tmp_path / "papers.csv"
    csv_path.write_text(REAL_PAPERS_WITH_DUPLICATE_DOI_CSV, encoding="utf-8")

    project = _new_project(database_path)
    workflow = GuiWorkflowService(database_path)

    outcome = workflow.import_and_screen(project.project_id, csv_path)

    assert outcome.total_input == 3
    assert outcome.unique_papers == 2
    assert outcome.duplicates_removed == 1
    assert outcome.screened_papers == 2
    assert outcome.included == 1
    assert outcome.excluded == 1

    data = GuiDataService(database_path)
    papers = data.papers()
    merged = next(p for p in papers if p.doi == "10.1038/nature21056")
    assert data.paper_details(str(merged.id))["provenance_count"] == 2


def test_export_report_after_real_import_reads_correctly(tmp_path: Path):
    """Pins the report-export path used by the Reports page: a report
    generated from a real persisted run should produce readable
    Markdown with human percentages, not the raw 0-1 floats that were
    still leaking through before this was fixed.
    """
    database_path = tmp_path / "psi.db"
    csv_path = tmp_path / "papers.csv"
    csv_path.write_text(REAL_PAPERS_WITH_DUPLICATE_DOI_CSV, encoding="utf-8")

    project = _new_project(database_path)
    workflow = GuiWorkflowService(database_path)
    workflow.import_and_screen(project.project_id, csv_path)

    data = GuiDataService(database_path)
    run_id = UUID(data.screening_runs()[0].run_id)

    export_dir = tmp_path / "export"
    export_dir.mkdir()
    json_path, markdown_path = workflow.export_report(run_id, export_dir)

    assert json_path.exists()
    assert markdown_path.exists()
    markdown = markdown_path.read_text(encoding="utf-8")
    assert "Inclusion rate: 50.00%" in markdown
    assert "0.5" not in markdown.split("Inclusion rate:")[1].split("\n")[0]
