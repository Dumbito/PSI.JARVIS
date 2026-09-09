from __future__ import annotations

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QGroupBox, QLabel, QLineEdit, QMainWindow, QPushButton, QTabWidget

from psi_jarvis.gui.i18n_manager import LANGUAGES, LanguageManager


def test_supported_languages_are_available(qapp):
    codes = {code for code, _ in LANGUAGES}
    assert {"en", "es", "fr", "de", "it", "pt", "ja", "zh", "ko"} <= codes


def test_language_manager_translates_entire_widget_tree(qapp):
    window = QMainWindow()
    window.setWindowTitle("Dashboard")
    label = QLabel("Projects", window)
    button = QPushButton("Close", window)
    group = QGroupBox("Settings", window)
    edit = QLineEdit(window)
    edit.setPlaceholderText("Research question")
    tabs = QTabWidget(window)
    tabs.addTab(QLabel("Overview"), "Overview")
    action = QAction("Refresh", window)
    window.addAction(action)
    window.show()
    qapp.processEvents()

    manager = LanguageManager(qapp)
    manager.set_language("es")
    manager.apply(window)

    assert window.windowTitle() == "Panel"
    assert label.text() == "Proyectos"
    assert button.text() == "Cerrar"
    assert group.title() == "Configuración"
    assert edit.placeholderText() == "Pregunta de investigación"
    assert tabs.tabText(0) == "Resumen"
    assert action.text() == "Actualizar"

    manager.set_language("en")
    manager.apply(window)
    assert window.windowTitle() == "Dashboard"
    assert label.text() == "Projects"
    assert button.text() == "Close"
    assert group.title() == "Settings"
    assert edit.placeholderText() == "Research question"
    assert tabs.tabText(0) == "Overview"
    assert action.text() == "Refresh"
    window.close()
