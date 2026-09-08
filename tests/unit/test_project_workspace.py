import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QTabWidget, QTableWidget

from psi_jarvis.gui.data import GuiDataService
from psi_jarvis.gui.project_workspace import ProjectPaperDialog, ProjectWorkspaceView
from psi_jarvis.gui.workflow import GuiWorkflowService


def test_project_workspace_paper_inspection(tmp_path):
    database_path = tmp_path / "psi.db"
    csv_path = tmp_path / "papers.csv"
    csv_path.write_text(
        "title,authors,abstract,doi,pmid,publication_year,journal\n"
        "Neural memory and cognition,Alice Smith,Study of cognition,,12345,2025,Journal of Cognition\n",
        encoding="utf-8",
    )
    workflow = GuiWorkflowService(database_path)
    project = workflow.create_project("Memory review", "How does neural memory support cognition?", "neural memory", ("cognition",), ())
    workflow.import_and_screen(project.project_id, csv_path)

    service = GuiDataService(database_path)
    app = QApplication.instance() or QApplication([])
    opened = []
    view = ProjectWorkspaceView(service, str(project.project_id), opened.append)
    paper_table = view.tabs.widget(1).findChild(QTableWidget)
    assert paper_table is not None
    assert paper_table.rowCount() == 1

    paper_table.selectRow(0)
    paper_table.doubleClicked.emit(paper_table.model().index(0, 1))
    assert isinstance(view._paper_dialog, ProjectPaperDialog)
    assert view._paper_dialog.paper_id == str(service.project_papers(str(project.project_id))[0].paper_id)

    view._paper_dialog.close()
    view.close()
    app.processEvents()


def test_project_paper_dialog_exposes_evidence_and_run_navigation(tmp_path):
    database_path = tmp_path / "psi.db"
    csv_path = tmp_path / "papers.csv"
    csv_path.write_text(
        "title,authors,abstract,doi,pmid,publication_year,journal\n"
        "Neural memory and cognition,Alice Smith,Study of cognition,,12345,2025,Journal of Cognition\n",
        encoding="utf-8",
    )
    workflow = GuiWorkflowService(database_path)
    project = workflow.create_project("Memory review", "Q", "neural memory", (), ())
    workflow.import_and_screen(project.project_id, csv_path)
    service = GuiDataService(database_path)
    project_id = str(project.project_id)
    paper_id = str(service.project_papers(project_id)[0].paper_id)

    app = QApplication.instance() or QApplication([])
    opened = []
    dialog = ProjectPaperDialog(service, project_id, paper_id, opened.append)
    tabs = dialog.findChild(QTabWidget)
    assert tabs is not None
    assert [tabs.tabText(i) for i in range(tabs.count())] == ["Metadata", "Abstract", "Screening", "Provenance", "Evidence"]
    assert service.paper_details(paper_id)["abstract"] == "Study of cognition"
    assert len(tuple(row for row in service.project_provenance(project_id) if row.paper_id == paper_id)) == 1

    screening_table = tabs.widget(2).findChild(QTableWidget)
    assert screening_table is not None
    assert screening_table.rowCount() == 1
    screening_table.selectRow(0)
    screening_table.doubleClicked.emit(screening_table.model().index(0, 3))
    assert opened == [service.project_screening_rows(project_id)[0].run_id]
    dialog.close()
    app.processEvents()


def test_project_scoped_queries_do_not_cross_project_boundaries(tmp_path):
    database_path = tmp_path / "psi.db"
    first_csv = tmp_path / "first.csv"
    second_csv = tmp_path / "second.csv"
    first_csv.write_text(
        "title,authors,abstract,doi,pmid,publication_year,journal\nFirst project paper,Alice,First abstract,,11111,2024,Journal One\n",
        encoding="utf-8",
    )
    second_csv.write_text(
        "title,authors,abstract,doi,pmid,publication_year,journal\nSecond project paper,Bob,Second abstract,,22222,2026,Journal Two\n",
        encoding="utf-8",
    )
    workflow = GuiWorkflowService(database_path)
    first = workflow.create_project("First", "Q1", "topic one", ("one",), ())
    second = workflow.create_project("Second", "Q2", "topic two", ("two",), ())
    workflow.import_and_screen(first.project_id, first_csv)
    workflow.import_and_screen(second.project_id, second_csv)

    service = GuiDataService(database_path)
    first_id = str(first.project_id)
    second_id = str(second.project_id)
    assert [p.title for p in service.project_papers(first_id)] == ["First project paper"]
    assert [p.title for p in service.project_papers(second_id)] == ["Second project paper"]
    assert [r.title for r in service.project_screening_rows(first_id)] == ["First project paper"]
    assert [r.title for r in service.project_screening_rows(second_id)] == ["Second project paper"]
    assert [p.title for p in service.project_provenance(first_id)] == ["First project paper"]
    assert [p.title for p in service.project_provenance(second_id)] == ["Second project paper"]
