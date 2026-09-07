import os
import sqlite3

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from psi_jarvis.gui.app import MainWindow
from psi_jarvis.gui.data import DashboardSnapshot, GuiDataService


def test_gui_data_without_database_is_safe(tmp_path):
    service = GuiDataService(tmp_path / "missing.db")
    snapshot = service.snapshot()
    assert snapshot == DashboardSnapshot()
    assert service.projects() == ()
    assert service.papers() == ()


def test_gui_data_with_uninitialized_database_is_safe(tmp_path):
    database_path = tmp_path / "uninitialized.db"
    with sqlite3.connect(database_path) as connection:
        connection.execute("CREATE TABLE unrelated (value TEXT)")

    service = GuiDataService(database_path)
    assert service.snapshot() == DashboardSnapshot()
    assert service.projects() == ()
    assert service.papers() == ()
    assert service.screening_rows() == ()
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
