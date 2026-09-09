from __future__ import annotations

from PySide6.QtWidgets import QLabel, QMainWindow, QPushButton, QTabWidget

from psi_jarvis.gui.i18n_manager import LANGUAGES, LanguageManager


def test_supported_languages_are_available(qapp):
    codes = {code for code, _ in LANGUAGES}
    assert {"en", "es", "fr", "de", "it", "pt", "ja", "zh", "ko"} <= codes


def test_language_manager_translates_entire_widget_tree(qapp):
    window = QMainWindow()
    window.setWindowTitle("Dashboard")
    label = QLabel("Projects", window)
    button = QPushButton("Close", window)
    tabs = QTabWidget(window)
    tabs.addTab(QLabel("Overview"), "Overview")
    window.show()
    qapp.processEvents()

    manager = LanguageManager(qapp)
    manager.set_language("es")
    manager.apply(window)

    assert window.windowTitle() == "Panel"
    assert label.text() == "Proyectos"
    assert button.text() == "Cerrar"
    assert tabs.tabText(0) == "Resumen"
    window.close()
