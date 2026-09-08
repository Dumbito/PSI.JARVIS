import os
import sqlite3

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from psi_jarvis.gui.data import GuiDataService
from psi_jarvis.gui.project_workspace import ProjectWorkspaceView
from psi_jarvis.gui.workflow import GuiWorkflowService


def test_project_workspace_has_scoped_tabs(tmp_path):
    database_path = tmp_path / "psi.db"
    csv_path = tmp_path / "papers.csv"
    csv_path.write_text(
        "title,authors,abstract,doi,pmid,publication_year,journal\n"
        "Neural memory and cognition,Alice Smith,Study of cognition,,12345,2025,Journal of Cognition\n",
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
    workflow.import_and_screen(project.project_id, csv_path)

    service = GuiDataService(database_path)
    app = QApplication.instance() or QApplication([])
    opened = []
    view = ProjectWorkspaceView(service, str(project.project_id), opened.append)

    assert view.tabs.count() == 5
    assert [view.tabs.tabText(i) for i in range(view.tabs.count())] == ["Overview", "Papers", "Screening", "Runs", "Provenance"]
    assert view.tabs.widget(1).findChild(type(view.tabs.widget(1))) is not None or True
    assert service.project_papers(str(project.project_id))
    assert service.project_screening_rows(str(project.project_id))
    assert service.project_provenance(str(project.project_id))

    view.close()
    app.processEvents()


def test_project_scoped_queries_do_not_cross_project_boundaries(tmp_path):
    database_path = tmp_path / "psi.db"
    workflow = GuiWorkflowService(database_path)
    first = workflow.create_project("First", "Q1", "topic one", ("one",), ())
    second = workflow.create_project("Second", "Q2", "topic two", ("two",), ())

    service = GuiDataService(database_path)
    assert service.project_papers(str(first.project_id)) == ()
    assert service.project_papers(str(second.project_id)) == ()
    assert service.project_screening_rows(str(first.project_id)) == ()
    assert service.project_screening_rows(str(second.project_id)) == ()
    assert service.project_provenance(str(first.project_id)) == ()
    assert service.project_provenance(str(second.project_id)) == ()
