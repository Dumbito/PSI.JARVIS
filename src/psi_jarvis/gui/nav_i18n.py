from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import QPushButton, QWidget


NAV_OBJECT_NAME = "nav"
_SOURCE_PROPERTY = "_psi_i18n_nav_source"
_ICON_PROPERTY = "_psi_i18n_nav_icon"


def translate_navigation_buttons(root: QWidget, translate: Callable[[str], str]) -> None:
    """Translate sidebar labels while keeping their decorative icon separate.

    Navigation buttons currently store icon + label in one display string.  We
    keep the original label/icon in widget properties so repeated language
    changes never try to translate an already-translated value.
    """
    for button in root.findChildren(QPushButton, NAV_OBJECT_NAME):
        source = button.property(_SOURCE_PROPERTY)
        icon = button.property(_ICON_PROPERTY)
        if source is None or icon is None:
            parts = button.text().split(maxsplit=1)
            if len(parts) != 2:
                continue
            icon, source = parts
            button.setProperty(_ICON_PROPERTY, icon)
            button.setProperty(_SOURCE_PROPERTY, source)
        button.setText(f"  {icon}   {translate(str(source))}")
