from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


class EmptyState(QWidget):
    """Compact action-oriented empty state for data-driven GUI pages."""

    def __init__(
        self,
        title: str,
        detail: str,
        action_text: str | None = None,
        action: Callable[[], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("emptyState")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(7)
        heading = QLabel(title)
        heading.setObjectName("sectionTitle")
        layout.addWidget(heading)
        description = QLabel(detail)
        description.setObjectName("pageSubtitle")
        description.setWordWrap(True)
        layout.addWidget(description)
        if action_text and action:
            button = QPushButton(action_text)
            button.clicked.connect(action)
            layout.addWidget(button)
        layout.addStretch()
