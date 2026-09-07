from __future__ import annotations

import sys
from typing import Callable

from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QProgressBar,
    QStackedWidget,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from psi_jarvis.gui.data import GuiDataService
from psi_jarvis.gui.theme import apply_theme


NAV_ITEMS = (
    ("Dashboard", "⌂"),
    ("Projects", "▣"),
    ("Papers", "▤"),
    ("Sources", "⇄"),
    ("Screening", "✓"),
    ("Analysis", "◫"),
    ("Reports", "▥"),
    ("Audit", "◇"),
    ("Settings", "⚙"),
)


def card(title: str | None = None) -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName("card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(16, 14, 16, 14)
    layout.setSpacing(8)
    if title:
        label = QLabel(title)
        label.setObjectName("sectionTitle")
        layout.addWidget(label)
    return frame, layout


def metric(label: str, value: int, accent: str = "") -> QFrame:
    frame, layout = card()
    value_label = QLabel(f"{value:,}")
    value_label.setObjectName("metricValue")
    label_label = QLabel(label)
    label_label.setObjectName("metricLabel")
    layout.addWidget(value_label)
    layout.addWidget(label_label)
    if accent:
        accent_label = QLabel(accent)
        accent_label.setObjectName("metricAccent")
        layout.addWidget(accent_label)
    return frame


class PlaceholderPage(QWidget):
    def __init__(self, title: str, subtitle: str, action: str | None = None) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 26)
        title_label = QLabel(title)
        title_label.setObjectName("pageTitle")
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("pageSubtitle")
        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)
        if action:
            button = QPushButton(action)
            button.setObjectName("primary")
            button.setMaximumWidth(200)
            layout.addWidget(button)
        layout.addStretch()


class DashboardPage(QWidget):
    def __init__(self, data: GuiDataService, refresh_callback: Callable[[], None]) -> None:
        super().__init__()
        self.data = data
        self.refresh_callback = refresh_callback
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(26, 24, 26, 26)
        self.layout.setSpacing(14)
        self._build()

    def _build(self) -> None:
        heading = QHBoxLayout()
        title = QLabel("Welcome to PSI.JARVIS")
        title.setObjectName("pageTitle")
        heading.addWidget(title)
        heading.addStretch()
        refresh = QPushButton("Refresh")
        refresh.setObjectName("secondary")
        refresh.clicked.connect(self.refresh_callback)
        heading.addWidget(refresh)
        self.layout.addLayout(heading)
        subtitle = QLabel("Scientific Paper Screening & Analysis System · deterministic · reproducible · auditable")
        subtitle.setObjectName("pageSubtitle")
        self.layout.addWidget(subtitle)

        snap = self.data.snapshot()
        grid = QGridLayout()
        grid.setSpacing(12)
        metrics = (
            ("Total papers", snap.papers, "Corpus"),
            ("Screened", snap.screened, "Decisions recorded"),
            ("Pending", snap.pending, "Awaiting screening"),
            ("Included", snap.included, "Accepted by rules"),
            ("Excluded", snap.excluded, "Rejected by rules"),
            ("Conflicts", snap.conflicts, "Human resolution"),
        )
        for index, (label, value, accent) in enumerate(metrics):
            grid.addWidget(metric(label, value, accent), index // 3, index % 3)
        self.layout.addLayout(grid)

        lower = QGridLayout()
        lower.setSpacing(12)
        progress_frame, progress_layout = card("Screening progress")
        percent = int((snap.screened / snap.papers) * 100) if snap.papers else 0
        bar = QProgressBar()
        bar.setValue(percent)
        progress_layout.addWidget(bar)
        progress_layout.addWidget(QLabel(f"{snap.screened:,} of {snap.papers:,} papers screened · {percent}%"))
        lower.addWidget(progress_frame, 0, 0)

        source_frame, source_layout = card("Acquisition sources")
        if snap.source_counts:
            for source, count in snap.source_counts:
                source_layout.addWidget(QLabel(f"{source}   ·   {count:,} records"))
        else:
            source_layout.addWidget(QLabel("No acquisition batches found yet."))
        lower.addWidget(source_frame, 0, 1)

        status_frame, status_layout = card("System status")
        status_layout.addWidget(QLabel(f"Database: {self.data.database_path}"))
        status_layout.addWidget(QLabel("Authority: deterministic screening engine"))
        status_layout.addWidget(QLabel("AI/NLP: auxiliary only · never primary screening authority"))
        lower.addWidget(status_frame, 1, 0, 1, 2)
        self.layout.addLayout(lower)
        self.layout.addStretch()


class ProjectsPage(QWidget):
    def __init__(self, data: GuiDataService) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 26)
        title = QLabel("Projects")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        layout.addWidget(QLabel("Review projects currently persisted in PSI.JARVIS."))
        table = QTableWidget(0, 4)
        table.setHorizontalHeaderLabels(["Project", "Topic", "Research question", "Created"])
        table.horizontalHeader().setStretchLastSection(True)
        projects = data.projects()
        table.setRowCount(len(projects))
        for row, project in enumerate(projects):
            values = [project.name, project.criteria.topic, project.research_question, project.created_at.isoformat()]
            for col, value in enumerate(values):
                table.setItem(row, col, QTableWidgetItem(str(value)))
        layout.addWidget(table)


class PapersPage(QWidget):
    def __init__(self, data: GuiDataService) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 26)
        top = QHBoxLayout()
        title = QLabel("Papers")
        title.setObjectName("pageTitle")
        top.addWidget(title)
        top.addStretch()
        search = QLineEdit()
        search.setPlaceholderText("Search title, DOI, PMID…")
        search.setMaximumWidth(300)
        top.addWidget(search)
        layout.addLayout(top)
        table = QTableWidget(0, 5)
        table.setHorizontalHeaderLabels(["Title", "Year", "Journal", "DOI", "PMID"])
        table.horizontalHeader().setStretchLastSection(True)
        papers = data.papers()
        table.setRowCount(len(papers))
        for row, paper in enumerate(papers):
            values = [paper.title, paper.publication_year or "—", paper.journal or "—", paper.doi or "—", paper.pmid or "—"]
            for col, value in enumerate(values):
                table.setItem(row, col, QTableWidgetItem(str(value)))
        layout.addWidget(table)


class SourcesPage(QWidget):
    def __init__(self, data: GuiDataService) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 26)
        title = QLabel("Sources")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        layout.addWidget(QLabel("Bibliographic connectors and their current local connection state."))
        for source in data.sources():
            frame, row = card()
            line = QHBoxLayout()
            name = QLabel(source.display_name)
            name.setMinimumWidth(180)
            state = QLabel(source.status.upper())
            state.setObjectName("metricAccent")
            line.addWidget(name)
            line.addWidget(state)
            line.addStretch()
            if source.detail:
                line.addWidget(QLabel(source.detail))
            row.addLayout(line)
            layout.addWidget(frame)
        layout.addStretch()


class ScreeningPage(QWidget):
    def __init__(self, data: GuiDataService) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 26)
        title = QLabel("Screening")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        layout.addWidget(QLabel("Human decisions are recorded here; the deterministic ScreeningEngine remains the authority."))
        controls = QHBoxLayout()
        selector = QComboBox()
        selector.addItems(["Pending", "Included", "Excluded", "All"])
        controls.addWidget(selector)
        controls.addStretch()
        layout.addLayout(controls)
        table = QTableWidget(0, 4)
        table.setHorizontalHeaderLabels(["Paper", "Year", "Decision", "Reason"])
        table.horizontalHeader().setStretchLastSection(True)
        papers = data.papers()
        table.setRowCount(min(len(papers), 100))
        for row, paper in enumerate(papers[:100]):
            table.setItem(row, 0, QTableWidgetItem(paper.title))
            table.setItem(row, 1, QTableWidgetItem(str(paper.publication_year or "—")))
            table.setItem(row, 2, QTableWidgetItem("Pending"))
            table.setItem(row, 3, QTableWidgetItem("Awaiting decision"))
        layout.addWidget(table)


class MainWindow(QMainWindow):
    def __init__(self, data_service: GuiDataService | None = None) -> None:
        super().__init__()
        self.setWindowTitle("PSI.JARVIS V.1")
        self.resize(1440, 900)
        self.setMinimumSize(1100, 700)
        self.data = data_service or GuiDataService()
        self.pages = QStackedWidget()
        self.nav_buttons: list[QPushButton] = []
        self._build_ui()
        self.statusBar().showMessage("Ready · deterministic scientific workspace")

    def _build_ui(self) -> None:
        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(214)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(14, 20, 14, 14)
        sidebar_layout.setSpacing(4)

        brand_row = QHBoxLayout()
        brand = QLabel("PSI.JARVIS")
        brand.setObjectName("brand")
        version = QLabel("V.1")
        version.setObjectName("version")
        brand_row.addWidget(brand)
        brand_row.addWidget(version)
        brand_row.addStretch()
        sidebar_layout.addLayout(brand_row)
        tagline = QLabel("Scientific Paper Screening\n& Analysis System")
        tagline.setObjectName("tagline")
        sidebar_layout.addWidget(tagline)
        sidebar_layout.addSpacing(16)

        for index, (label, icon) in enumerate(NAV_ITEMS):
            button = QPushButton(f"  {icon}   {label}")
            button.setObjectName("nav")
            button.setProperty("active", index == 0)
            button.clicked.connect(lambda checked=False, i=index: self._select_page(i))
            self.nav_buttons.append(button)
            sidebar_layout.addWidget(button)

        sidebar_layout.addStretch()
        footer = QLabel("Human methodological authority\n\nDeterministic · Traceable\nReproducible")
        footer.setObjectName("tagline")
        sidebar_layout.addWidget(footer)
        root_layout.addWidget(sidebar)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        self.pages.addWidget(DashboardPage(self.data, self.refresh_dashboard))
        self.pages.addWidget(ProjectsPage(self.data))
        self.pages.addWidget(PapersPage(self.data))
        self.pages.addWidget(SourcesPage(self.data))
        self.pages.addWidget(ScreeningPage(self.data))
        self.pages.addWidget(PlaceholderPage("Analysis", "Statistical and screening analyses produced by the existing analysis layer.", "Open analysis workspace"))
        self.pages.addWidget(PlaceholderPage("Reports", "Generate and export reproducible scientific report packages.", "Build report"))
        self.pages.addWidget(PlaceholderPage("Audit", "Trace decisions, provenance, metadata changes and execution history."))
        self.pages.addWidget(PlaceholderPage("Settings", "Application and source configuration. Secrets remain outside the GUI source tree."))
        content_layout.addWidget(self.pages)
        root_layout.addWidget(content, 1)
        self.setCentralWidget(root)
        self.setStatusBar(QStatusBar())

    def _select_page(self, index: int) -> None:
        self.pages.setCurrentIndex(index)
        for i, button in enumerate(self.nav_buttons):
            button.setProperty("active", i == index)
            button.style().unpolish(button)
            button.style().polish(button)

    def refresh_dashboard(self) -> None:
        old = self.pages.widget(0)
        self.pages.removeWidget(old)
        old.deleteLater()
        self.pages.insertWidget(0, DashboardPage(self.data, self.refresh_dashboard))
        self._select_page(0)
        self.statusBar().showMessage("Dashboard refreshed")


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("PSI.JARVIS")
    app.setApplicationVersion("0.1.0")
    apply_theme(app)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
