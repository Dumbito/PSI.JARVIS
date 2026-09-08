from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)


@dataclass(frozen=True)
class TutorialStep:
    title: str
    body: str
    page: str


STEPS = (
    TutorialStep(
        "Welcome to PSI.JARVIS",
        "A reproducible workspace for scientific paper acquisition, deterministic screening, analysis, provenance and reporting. The scientific rules live outside the GUI.",
        "Workspace",
    ),
    TutorialStep(
        "1 · Create a project",
        "Start in Projects and define the research question, topic, inclusion rules and exclusion rules. The protocol is validated by the application/domain layer.",
        "Projects",
    ),
    TutorialStep(
        "2 · Import your corpus",
        "Use Papers → Import & screen to load CSV, Excel or RIS files. PSI.JARVIS normalizes metadata, removes duplicates and sends the corpus through the same screening pipeline used by the rest of the system.",
        "Papers",
    ),
    TutorialStep(
        "3 · Review evidence",
        "Screening shows persisted decisions and criteria versions. Analysis exposes metadata quality, rules, exclusions, deduplication, authors, journals and publication years.",
        "Screening / Analysis",
    ),
    TutorialStep(
        "4 · Trace everything",
        "Sources shows acquisition status, Audit shows metadata-change history, and provenance is retained across acquisition and synchronization. Conflicts are not silently resolved.",
        "Sources / Audit",
    ),
    TutorialStep(
        "5 · Export the result",
        "Reports uses the existing reporting layer to generate JSON and Markdown from persisted screening evidence. The GUI does not rerun or reinterpret scientific decisions.",
        "Reports",
    ),
)


class TutorialDialog(QDialog):
    """First-class onboarding shown at every application launch."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("PSI.JARVIS · Quick tutorial")
        self.setModal(True)
        self.resize(720, 440)
        self.setMinimumSize(620, 380)
        self._index = 0

        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 24)
        root.setSpacing(16)

        eyebrow = QLabel("GETTING STARTED")
        eyebrow.setObjectName("tutorialEyebrow")
        root.addWidget(eyebrow)

        self.stack = QStackedWidget()
        for step in STEPS:
            page = QWidget()
            layout = QVBoxLayout(page)
            layout.setContentsMargins(0, 8, 0, 8)
            layout.setSpacing(14)
            title = QLabel(step.title)
            title.setObjectName("tutorialTitle")
            title.setWordWrap(True)
            body = QLabel(step.body)
            body.setObjectName("tutorialBody")
            body.setWordWrap(True)
            body.setAlignment(Qt.AlignTop | Qt.AlignLeft)
            destination = QLabel(f"Open: {step.page}")
            destination.setObjectName("tutorialDestination")
            layout.addWidget(title)
            layout.addWidget(body)
            layout.addWidget(destination)
            layout.addStretch()
            self.stack.addWidget(page)
        root.addWidget(self.stack, 1)

        self.progress = QLabel()
        self.progress.setObjectName("tutorialProgress")
        root.addWidget(self.progress)

        buttons = QHBoxLayout()
        self.skip_button = QPushButton("Skip")
        self.skip_button.setObjectName("secondary")
        self.skip_button.clicked.connect(self.reject)
        self.close_button = QPushButton("Close")
        self.close_button.setObjectName("secondary")
        self.close_button.clicked.connect(self.reject)
        self.back_button = QPushButton("Back")
        self.back_button.setObjectName("secondary")
        self.back_button.clicked.connect(self._back)
        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self._next)
        buttons.addWidget(self.skip_button)
        buttons.addWidget(self.close_button)
        buttons.addStretch()
        buttons.addWidget(self.back_button)
        buttons.addWidget(self.next_button)
        root.addLayout(buttons)
        self._update()

    def _update(self) -> None:
        self.stack.setCurrentIndex(self._index)
        self.progress.setText(f"Step {self._index + 1} of {len(STEPS)}")
        self.back_button.setEnabled(self._index > 0)
        self.next_button.setText("Finish" if self._index == len(STEPS) - 1 else "Next")

    def _back(self) -> None:
        if self._index > 0:
            self._index -= 1
            self._update()

    def _next(self) -> None:
        if self._index >= len(STEPS) - 1:
            self.accept()
            return
        self._index += 1
        self._update()
