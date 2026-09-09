"""A Spotlight/Linear-style command palette (Ctrl+K).

Lets the user jump to any sidebar page or trigger a small set of
frequent actions without touching the mouse, by typing a few letters
and pressing Enter. Read-only with respect to scientific data - it
only navigates the GUI or opens existing dialogs/actions, never
creates or mutates persisted state on its own.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
)

from psi_jarvis.gui.nav_icons import nav_icon


@dataclass(frozen=True)
class Command:
    title: str
    subtitle: str
    icon_label: str
    run: Callable[[], None]


class CommandPalette(QDialog):
    def __init__(self, commands: tuple[Command, ...], parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("commandPalette")
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setWindowFlag(Qt.Popup)
        self.setModal(False)
        self._commands = commands

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.query = QLineEdit()
        self.query.setObjectName("paletteQuery")
        self.query.setPlaceholderText("Jump to a page or action…")
        self.query.textChanged.connect(self._filter)
        self.query.installEventFilter(self)
        layout.addWidget(self.query)

        self.list = QListWidget()
        self.list.setObjectName("paletteList")
        self.list.itemActivated.connect(self._activate_item)
        layout.addWidget(self.list)

        self._populate(commands)
        self.resize(460, 360)

    def _populate(self, commands: tuple[Command, ...]) -> None:
        self.list.clear()
        for command in commands:
            item = QListWidgetItem(
                nav_icon(command.icon_label, "#dce7f5", 20), command.title
            )
            item.setData(Qt.UserRole, command)
            if command.subtitle:
                item.setToolTip(command.subtitle)
            self.list.addItem(item)
        if self.list.count():
            self.list.setCurrentRow(0)

    def _filter(self, text: str) -> None:
        needle = text.strip().lower()
        matches = tuple(
            c
            for c in self._commands
            if needle in c.title.lower() or needle in c.subtitle.lower()
        )
        self._populate(matches if needle else self._commands)

    def _activate_item(self, item: QListWidgetItem) -> None:
        command: Command = item.data(Qt.UserRole)
        self.close()
        command.run()

    def eventFilter(self, obj, event):
        if obj is self.query and event.type() == event.Type.KeyPress:
            key = event.key()
            if key == Qt.Key_Down:
                self.list.setCurrentRow(
                    min(self.list.currentRow() + 1, self.list.count() - 1)
                )
                return True
            if key == Qt.Key_Up:
                self.list.setCurrentRow(max(self.list.currentRow() - 1, 0))
                return True
            if key in (Qt.Key_Return, Qt.Key_Enter):
                item = self.list.currentItem()
                if item is not None:
                    self._activate_item(item)
                return True
            if key == Qt.Key_Escape:
                self.close()
                return True
        return super().eventFilter(obj, event)

    def show_centered_on(self, widget) -> None:
        geo = widget.geometry()
        top_left = widget.mapToGlobal(geo.topLeft())
        x = top_left.x() + (geo.width() - self.width()) // 2
        y = top_left.y() + 120
        self.move(x, y)
        self.query.clear()
        self.show()
        self.query.setFocus()
