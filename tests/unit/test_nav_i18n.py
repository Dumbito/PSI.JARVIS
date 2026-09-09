from __future__ import annotations

from PySide6.QtWidgets import QPushButton, QWidget, QVBoxLayout

from psi_jarvis.gui.nav_i18n import translate_navigation_buttons


def test_navigation_button_translates_label_without_translating_icon(qapp):
    root = QWidget()
    layout = QVBoxLayout(root)
    button = QPushButton("  ⌂   Dashboard", root)
    button.setObjectName("nav")
    layout.addWidget(button)
    root.show()
    qapp.processEvents()

    catalog = {"Dashboard": "Panel"}
    translate_navigation_buttons(root, lambda text: catalog.get(text, text))
    assert button.text() == "  ⌂   Panel"

    translate_navigation_buttons(root, lambda text: {"Dashboard": "Proyectos"}.get(text, text))
    assert button.text() == "  ⌂   Proyectos"

    translate_navigation_buttons(root, lambda text: text)
    assert button.text() == "  ⌂   Dashboard"
    root.close()
