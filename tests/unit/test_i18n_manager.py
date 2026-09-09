from __future__ import annotations

from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QGroupBox,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTabWidget,
)

from psi_jarvis.gui.i18n_manager import LANGUAGES, LanguageManager
from psi_jarvis.gui.nav_icons import nav_icon


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


def test_language_manager_translates_sidebar_nav_buttons_without_losing_icon(qapp):
    """Regression test: nav buttons render a real QIcon plus a plain
    text label (no icon glyph embedded in the string), so the generic
    exact-match catalog lookup must translate them like any other
    button while the icon itself is untouched.
    """
    window = QMainWindow()
    nav_button = QPushButton("Dashboard", window)
    nav_button.setObjectName("nav")
    icon = nav_icon("Dashboard", "#dce7f5")
    nav_button.setIcon(icon)
    window.setCentralWidget(nav_button)
    window.show()
    qapp.processEvents()

    manager = LanguageManager(qapp)
    manager.set_language("es")

    assert nav_button.text() == "Panel"
    assert nav_button.icon().cacheKey() == icon.cacheKey()

    manager.set_language("en")
    assert nav_button.text() == "Dashboard"
    window.close()
