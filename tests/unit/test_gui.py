import os
import sqlite3

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from psi_jarvis.gui.app import MainWindow
from psi_jarvis.gui.data import DashboardSnapshot, GuiDataService, MetadataQualitySnapshot
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
