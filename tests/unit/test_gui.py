import os

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


def test_main_window_builds_without_touching_core_logic(tmp_path):
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.data = GuiDataService(tmp_path / "missing.db")
    assert window.windowTitle() == "PSI.JARVIS V.1"
    assert window.pages.count() == 9
    assert len(window.nav_buttons) == 9
    window.close()
    app.processEvents()
