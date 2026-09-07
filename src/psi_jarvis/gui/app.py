from __future__ import annotations

import sys
from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QStackedWidget,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from psi_jarvis.gui.data import GuiDataService
from psi_jarvis.gui.theme import apply_theme

NAV_ITEMS = (
    ("Dashboard", "⌂"), ("Projects", "▣"), ("Papers", "▤"),
    ("Sources", "⇄"), ("Screening", "✓"), ("Analysis", "◫"),
    ("Reports", "▥"), ("Audit", "◇"), ("Settings", "⚙"),
)


def page_header(title: str, subtitle: str) -> QVBoxLayout:
    layout = QVBoxLayout()
    layout.setSpacing(4)
    title_label = QLabel(title)
    title_label.setObjectName("pageTitle")
    subtitle_label = QLabel(subtitle)
    subtitle_label.setObjectName("pageSubtitle")
    layout.addWidget(title_label)
    layout.addWidget(subtitle_label)
    return layout


def card(title: str | None = None) -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName("card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(16, 14, 16, 14)
    layout.setSpacing(9)
    if title:
        label = QLabel(title)
        label.setObjectName("sectionTitle")
        layout.addWidget(label)
    return frame, layout


def metric(label: str, value: int, accent: str) -> QFrame:
    frame, layout = card()
    value_label = QLabel(f"{value:,}")
    value_label.setObjectName("metricValue")
    label_label = QLabel(label)
    label_label.setObjectName("metricLabel")
    accent_label = QLabel(accent)
    accent_label.setObjectName("metricAccent")
    layout.addWidget(value_label)
    layout.addWidget(label_label)
    layout.addWidget(accent_label)
    return frame


class PaperDialog(QDialog):
    def __init__(self, details: dict, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Paper details")
        self.resize(760, 600)
        layout = QVBoxLayout(self)
        title = QLabel(details["title"])
        title.setObjectName("dialogTitle")
        title.setWordWrap(True)
        layout.addWidget(title)
        metadata, metadata_layout = card()
        metadata_layout.addWidget(QLabel(f"Authors: {details['authors'] or '—'}"))
        metadata_layout.addWidget(QLabel(f"Journal: {details['journal'] or '—'} · Year: {details['year'] or '—'}"))
        metadata_layout.addWidget(QLabel(f"DOI: {details['doi'] or '—'} · PMID: {details['pmid'] or '—'}"))
        metadata_layout.addWidget(QLabel(f"Provenance records: {details['provenance_count']}"))
        layout.addWidget(metadata)
        abstract = QTextEdit()
        abstract.setReadOnly(True)
        abstract.setPlainText(details["abstract"] or "No abstract stored.")
        layout.addWidget(abstract, 1)
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class DashboardPage(QWidget):
    def __init__(self, data: GuiDataService, refresh: Callable[[], None]) -> None:
        super().__init__()
        self.data = data
        self.refresh = refresh
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(28, 24, 28, 28)
        self.root.setSpacing(14)
        self.rebuild()

    def rebuild(self) -> None:
        while self.root.count():
            item = self.root.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    child = item.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
        heading = QHBoxLayout()
        title = QLabel("Research workspace")
        title.setObjectName("pageTitle")
        heading.addWidget(title)
        heading.addStretch()
        refresh = QPushButton("Refresh")
        refresh.setObjectName("secondary")
        refresh.clicked.connect(self.refresh)
        heading.addWidget(refresh)
        self.root.addLayout(heading)
        self.root.addWidget(QLabel("A reproducible workspace for scientific paper acquisition, screening and provenance."), 0)
        snap = self.data.snapshot()
        grid = QGridLayout(); grid.setSpacing(12)
        metrics = (
            ("Projects", snap.projects, "Review workspaces"),
            ("Papers", snap.papers, "Persisted corpus"),
            ("Screened", snap.screened, "Recorded results"),
            ("Pending", snap.pending, "Awaiting screening"),
            ("Included", snap.included, "Accepted"),
            ("Excluded", snap.excluded, "Rejected"),
        )
        for i, values in enumerate(metrics):
            grid.addWidget(metric(*values), i // 3, i % 3)
        self.root.addLayout(grid)
        lower = QGridLayout(); lower.setSpacing(12)
        progress, progress_layout = card("Screening progress")
        percent = int(snap.screened / snap.papers * 100) if snap.papers else 0
        bar = QProgressBar(); bar.setValue(percent); bar.setFormat(f"{percent}%")
        progress_layout.addWidget(bar)
        progress_layout.addWidget(QLabel(f"{snap.screened:,} of {snap.papers:,} papers have persisted screening results."))
        lower.addWidget(progress, 0, 0)
        sources, source_layout = card("Acquisition footprint")
        if snap.source_counts:
            for source, count in snap.source_counts:
                source_layout.addWidget(QLabel(f"{source.upper()}  ·  {count:,} acquisition batch(es)"))
        else:
            source_layout.addWidget(QLabel("No acquisition batches recorded."))
        lower.addWidget(sources, 0, 1)
        integrity, integrity_layout = card("Methodological boundary")
        integrity_layout.addWidget(QLabel("Authority: deterministic ScreeningEngine"))
        integrity_layout.addWidget(QLabel("Provenance: retained across acquisition and synchronization"))
        integrity_layout.addWidget(QLabel("AI/NLP: auxiliary only; never silently changes scientific decisions"))
        lower.addWidget(integrity, 1, 0, 1, 2)
        self.root.addLayout(lower)
        self.root.addStretch()


class ProjectsPage(QWidget):
    def __init__(self, data: GuiDataService) -> None:
        super().__init__(); self.data = data
        root = QVBoxLayout(self); root.setContentsMargins(28,24,28,28); root.setSpacing(14)
        root.addLayout(page_header("Projects", "Review protocols persisted in the project repository."))
        table = QTableWidget(0, 4); table.setObjectName("dataTable")
        table.setHorizontalHeaderLabels(["Project", "Topic", "Research question", "Created"])
        table.horizontalHeader().setStretchLastSection(True); table.setSelectionBehavior(QTableWidget.SelectRows)
        projects = data.projects(); table.setRowCount(len(projects))
        for row, project in enumerate(projects):
            values = [project.name, project.criteria.topic, project.research_question, project.created_at.isoformat()]
            for col, value in enumerate(values): table.setItem(row, col, QTableWidgetItem(str(value)))
        root.addWidget(table, 1)
        note = QLabel("Project editing remains outside this read-only presentation layer; protocol semantics are owned by the application/domain layer.")
        note.setObjectName("pageSubtitle"); root.addWidget(note)


class PapersPage(QWidget):
    def __init__(self, data: GuiDataService) -> None:
        super().__init__(); self.data = data
        root = QVBoxLayout(self); root.setContentsMargins(28,24,28,28); root.setSpacing(12)
        top = QHBoxLayout(); title = QLabel("Papers"); title.setObjectName("pageTitle"); top.addWidget(title); top.addStretch()
        self.search = QLineEdit(); self.search.setPlaceholderText("Search title, DOI, PMID, journal…"); self.search.setMaximumWidth(360); top.addWidget(self.search)
        root.addLayout(top)
        self.table = QTableWidget(0, 5); self.table.setHorizontalHeaderLabels(["Title","Year","Journal","DOI","PMID"])
        self.table.horizontalHeader().setStretchLastSection(True); self.table.setSelectionBehavior(QTableWidget.SelectRows); self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.doubleClicked.connect(self.open_selected)
        self.search.textChanged.connect(self.filter_rows); root.addWidget(self.table, 1)
        self.rows = data.papers(); self.populate()
        hint = QLabel("Double-click a paper to inspect its stored metadata and provenance count."); hint.setObjectName("pageSubtitle"); root.addWidget(hint)

    def populate(self) -> None:
        self.table.setRowCount(len(self.rows))
        for row, paper in enumerate(self.rows):
            values = [paper.title, paper.publication_year or "—", paper.journal or "—", paper.doi or "—", paper.pmid or "—"]
            item = QTableWidgetItem(str(paper.id)); item.setData(Qt.UserRole, str(paper.id))
            for col, value in enumerate(values): self.table.setItem(row, col, QTableWidgetItem(str(value)))
            self.table.item(row, 0).setData(Qt.UserRole, str(paper.id))

    def filter_rows(self, text: str) -> None:
        query = text.casefold().strip()
        for row in range(self.table.rowCount()):
            haystack = " ".join(self.table.item(row, col).text() for col in range(self.table.columnCount())).casefold()
            self.table.setRowHidden(row, query not in haystack)

    def open_selected(self) -> None:
        row = self.table.currentRow()
        if row < 0: return
        paper_id = self.table.item(row, 0).data(Qt.UserRole)
        details = self.data.paper_details(paper_id)
        if details: PaperDialog(details, self).exec()


class SourcesPage(QWidget):
    def __init__(self, data: GuiDataService) -> None:
        super().__init__(); self.data = data
        root = QVBoxLayout(self); root.setContentsMargins(28,24,28,28); root.setSpacing(12)
        top = QHBoxLayout(); top.addLayout(page_header("Sources", "Connection visibility for bibliographic acquisition.")); top.addStretch()
        refresh = QPushButton("Refresh sources"); refresh.setObjectName("secondary"); refresh.clicked.connect(self.rebuild); top.addWidget(refresh); root.addLayout(top)
        self.list = QListWidget(); self.list.setSpacing(6); root.addWidget(self.list, 1); self.rebuild()

    def rebuild(self) -> None:
        self.list.clear()
        for source in self.data.sources():
            item = QListWidgetItem(f"{source.display_name}    ·    {source.status.upper()}" + (f"    ·    {source.detail}" if source.detail else ""))
            item.setToolTip(f"Source key: {source.key}\nStatus: {source.status}\n{source.detail}")
            self.list.addItem(item)


class ScreeningPage(QWidget):
    def __init__(self, data: GuiDataService) -> None:
        super().__init__(); self.data = data
        root = QVBoxLayout(self); root.setContentsMargins(28,24,28,28); root.setSpacing(12)
        top = QHBoxLayout(); title = QLabel("Screening"); title.setObjectName("pageTitle"); top.addWidget(title); top.addStretch()
        self.filter = QComboBox(); self.filter.addItems(["All decisions","Included","Excluded"]); self.filter.currentTextChanged.connect(self.apply_filter); top.addWidget(self.filter); root.addLayout(top)
        root.addWidget(QLabel("Persisted screening results are displayed as evidence. The GUI does not create or alter scientific decisions."))
        self.table = QTableWidget(0, 5); self.table.setHorizontalHeaderLabels(["Paper","Year","Decision","Reason","Criteria version"]); self.table.horizontalHeader().setStretchLastSection(True); self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        root.addWidget(self.table, 1); self.rows = data.screening_rows(); self.populate()

    def populate(self) -> None:
        self.table.setRowCount(len(self.rows))
        for row, result in enumerate(self.rows):
            values = [result.title, result.year or "—", result.decision, result.reason, result.criteria_version or "—"]
            for col, value in enumerate(values): self.table.setItem(row, col, QTableWidgetItem(str(value)))
        self.apply_filter(self.filter.currentText())

    def apply_filter(self, value: str) -> None:
        for row in range(self.table.rowCount()):
            decision = self.table.item(row, 2).text()
            self.table.setRowHidden(row, value != "All decisions" and decision != value)


class AnalysisPage(QWidget):
    def __init__(self, data: GuiDataService) -> None:
        super().__init__(); root = QVBoxLayout(self); root.setContentsMargins(28,24,28,28); root.setSpacing(14)
        root.addLayout(page_header("Analysis", "Read-only presentation of analysis capabilities built on the deterministic pipeline."))
        for title, text in (("Screening metrics","Decision distribution, rule analysis, sensitivity and configuration comparison."),("Metadata quality","Completeness and provenance indicators can be surfaced here without changing source records."),("Future auxiliary intelligence","NLP/AI belongs to Fase 8 and will remain subordinate to validated deterministic outputs.")):
            frame, layout = card(title); layout.addWidget(QLabel(text)); root.addWidget(frame)
        root.addStretch()


class ReportsPage(QWidget):
    def __init__(self, data: GuiDataService) -> None:
        super().__init__(); root = QVBoxLayout(self); root.setContentsMargins(28,24,28,28); root.setSpacing(14)
        root.addLayout(page_header("Reports", "Reproducible report generation remains backed by the existing reporting layer."))
        frame, layout = card("Available report surfaces")
        for text in ("Markdown renderer", "JSON renderer", "Report package model", "Export layer"):
            layout.addWidget(QLabel("•  " + text))
        root.addWidget(frame)
        root.addWidget(QLabel("Report execution is intentionally not duplicated inside the GUI; the desktop layer will call the application services when an end-to-end report action is enabled."))
        root.addStretch()


class AuditPage(QWidget):
    def __init__(self, data: GuiDataService) -> None:
        super().__init__(); self.data = data
        root = QVBoxLayout(self); root.setContentsMargins(28,24,28,28); root.setSpacing(12)
        top = QHBoxLayout(); top.addLayout(page_header("Audit", "Metadata-change history and provenance evidence.")); top.addStretch()
        refresh = QPushButton("Refresh"); refresh.setObjectName("secondary"); refresh.clicked.connect(self.populate); top.addWidget(refresh); root.addLayout(top)
        self.table = QTableWidget(0, 4); self.table.setHorizontalHeaderLabels(["Changed at","Paper ID","Source","Changed fields"]); self.table.horizontalHeader().setStretchLastSection(True); self.table.setEditTriggers(QTableWidget.NoEditTriggers); root.addWidget(self.table,1); self.populate()

    def populate(self) -> None:
        rows = self.data.audit_rows(); self.table.setRowCount(len(rows))
        for row, audit in enumerate(rows):
            values = [audit.changed_at, audit.paper_id, audit.source_key, ", ".join(audit.changed_fields)]
            for col, value in enumerate(values): self.table.setItem(row,col,QTableWidgetItem(value))


class SettingsPage(QWidget):
    def __init__(self, data: GuiDataService) -> None:
        super().__init__(); root = QVBoxLayout(self); root.setContentsMargins(28,24,28,28); root.setSpacing(14)
        root.addLayout(page_header("Settings", "Runtime paths and methodological safeguards."))
        db, db_layout = card("Database")
        db_layout.addWidget(QLabel(str(data.database_path)))
        db_layout.addWidget(QLabel("Override with PSI_JARVIS_DATABASE_PATH when launching the application."))
        root.addWidget(db)
        boundary, boundary_layout = card("Scientific safeguards")
        boundary_layout.addWidget(QLabel("Deterministic screening remains authoritative."))
        boundary_layout.addWidget(QLabel("Synchronization never resolves metadata conflicts silently."))
        boundary_layout.addWidget(QLabel("Credentials and tokens are kept outside the source tree."))
        root.addWidget(boundary)
        root.addStretch()


class MainWindow(QMainWindow):
    def __init__(self, data_service: GuiDataService | None = None) -> None:
        super().__init__()
        self.setWindowTitle("PSI.JARVIS V.1")
        self.resize(1440, 900); self.setMinimumSize(1100, 700)
        self.data = data_service or GuiDataService()
        self.pages = QStackedWidget(); self.nav_buttons: list[QPushButton] = []
        self._build_ui(); self.statusBar().showMessage("Ready · deterministic scientific workspace")

    def _build_ui(self) -> None:
        root = QWidget(); root_layout = QHBoxLayout(root); root_layout.setContentsMargins(0,0,0,0); root_layout.setSpacing(0)
        sidebar = QFrame(); sidebar.setObjectName("sidebar"); sidebar.setFixedWidth(220); side = QVBoxLayout(sidebar); side.setContentsMargins(14,20,14,14); side.setSpacing(4)
        brand = QHBoxLayout(); brand_label = QLabel("PSI.JARVIS"); brand_label.setObjectName("brand"); version = QLabel("V.1"); version.setObjectName("version"); brand.addWidget(brand_label); brand.addWidget(version); brand.addStretch(); side.addLayout(brand)
        tagline = QLabel("Scientific Paper Screening\n& Analysis System"); tagline.setObjectName("tagline"); side.addWidget(tagline); side.addSpacing(16)
        for index, (label, icon) in enumerate(NAV_ITEMS):
            button = QPushButton(f"  {icon}   {label}"); button.setObjectName("nav"); button.setProperty("active", index == 0); button.clicked.connect(lambda checked=False, i=index: self._select_page(i)); self.nav_buttons.append(button); side.addWidget(button)
        side.addStretch(); footer = QLabel("Human methodological authority\n\nDeterministic · Traceable\nReproducible"); footer.setObjectName("tagline"); side.addWidget(footer); root_layout.addWidget(sidebar)
        content = QWidget(); content_layout = QVBoxLayout(content); content_layout.setContentsMargins(0,0,0,0)
        self.pages.addWidget(DashboardPage(self.data, self.refresh_dashboard))
        self.pages.addWidget(ProjectsPage(self.data)); self.pages.addWidget(PapersPage(self.data)); self.pages.addWidget(SourcesPage(self.data)); self.pages.addWidget(ScreeningPage(self.data)); self.pages.addWidget(AnalysisPage(self.data)); self.pages.addWidget(ReportsPage(self.data)); self.pages.addWidget(AuditPage(self.data)); self.pages.addWidget(SettingsPage(self.data))
        content_layout.addWidget(self.pages); root_layout.addWidget(content,1); self.setCentralWidget(root); self.setStatusBar(QStatusBar())

    def _select_page(self, index: int) -> None:
        self.pages.setCurrentIndex(index)
        for i, button in enumerate(self.nav_buttons):
            button.setProperty("active", i == index); button.style().unpolish(button); button.style().polish(button)
        self.statusBar().showMessage(f"{NAV_ITEMS[index][0]} · ready")

    def refresh_dashboard(self) -> None:
        old = self.pages.widget(0); self.pages.removeWidget(old); old.deleteLater(); self.pages.insertWidget(0, DashboardPage(self.data, self.refresh_dashboard)); self._select_page(0); self.statusBar().showMessage("Dashboard refreshed")


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    apply_theme(app)
    window = MainWindow(); window.show()
    return app.exec()
