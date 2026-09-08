import os
import sqlite3

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from psi_jarvis.gui.app import MainWindow
from psi_jarvis.gui.data import DashboardSnapshot, GuiDataService, MetadataQualitySnapshot
from psi_jarvis.gui.workflow import GuiWorkflowService
from psi_jarvis.infrastructure.sqlite_migrations import initialize_schema


def test_gui_data_without_database_is_safe(tmp_path):
    service = GuiDataService(tmp_path / "missing.db")
    snapshot = service.snapshot()
    assert snapshot == DashboardSnapshot()
    assert service.projects() == ()
    assert service.papers() == ()
    assert service.screening_runs() == ()
    assert service.metadata_quality() == MetadataQualitySnapshot()


def test_gui_data_with_uninitialized_database_is_safe(tmp_path):
    database_path = tmp_path / "uninitialized.db"
    with sqlite3.connect(database_path) as connection:
        connection.execute("CREATE TABLE unrelated (value TEXT)")

    service = GuiDataService(database_path)
    assert service.snapshot() == DashboardSnapshot()
    assert service.projects() == ()
    assert service.papers() == ()
    assert service.screening_rows() == ()
    assert service.screening_runs() == ()
    assert service.metadata_quality() == MetadataQualitySnapshot()
    assert service.audit_rows() == ()
    assert service.paper_details("not-a-uuid") is None


def test_main_window_builds_with_injected_data_service(tmp_path):
    app = QApplication.instance() or QApplication([])
    service = GuiDataService(tmp_path / "missing.db")
    window = MainWindow(data_service=service)
    assert window.windowTitle() == "PSI.JARVIS V.1"
    assert window.pages.count() == 9
    assert len(window.nav_buttons) == 9
    assert window.data is service
    window.close()
    app.processEvents()


def test_main_window_navigation_updates_active_page(tmp_path):
    app = QApplication.instance() or QApplication([])
    window = MainWindow(data_service=GuiDataService(tmp_path / "missing.db"))
    window.nav_buttons[5].click()
    assert window.pages.currentIndex() == 5
    assert window.nav_buttons[5].property("active") is True
    assert window.nav_buttons[0].property("active") is False
    window.close()
    app.processEvents()


def test_main_window_builds_against_initialized_schema(tmp_path):
    database_path = tmp_path / "psi.db"
    with sqlite3.connect(database_path) as connection:
        initialize_schema(connection)
        connection.commit()

    app = QApplication.instance() or QApplication([])
    window = MainWindow(data_service=GuiDataService(database_path))
    assert window.pages.count() == 9
    assert window.data.snapshot() == DashboardSnapshot()
    assert window.data.metadata_quality() == MetadataQualitySnapshot()
    window.close()
    app.processEvents()


def test_gui_workflow_creates_project_imports_and_screens_csv(tmp_path):
    database_path = tmp_path / "psi.db"
    csv_path = tmp_path / "papers.csv"
    csv_path.write_text(
        "title,authors,abstract,doi,pmid,publication_year,journal\n"
        "Neural memory and cognition,Alice Smith;Bob Jones,Study of neural memory,,12345,2025,Journal of Cognition\n",
        encoding="utf-8",
    )

    workflow = GuiWorkflowService(database_path)
    project = workflow.create_project(
        name="Memory review",
        research_question="How does neural memory support cognition?",
        topic="neural memory",
        inclusion=("cognition",),
        exclusion=(),
    )

    outcome = workflow.import_and_screen(project.project_id, csv_path)

    assert outcome.total_input == 1
    assert outcome.unique_papers == 1
    assert outcome.duplicates_removed == 0
    assert outcome.screened_papers == 1
    assert outcome.included == 1
    assert outcome.excluded == 0

    service = GuiDataService(database_path)
    snapshot = service.snapshot()
    assert snapshot.projects == 1
    assert snapshot.papers == 1
    assert snapshot.screened == 1
    assert snapshot.included == 1
    assert snapshot.excluded == 0
    assert len(service.screening_rows()) == 1
    assert len(service.screening_runs()) == 1
    assert service.metadata_quality().with_abstract == 1
    assert service.metadata_quality().with_doi == 0
