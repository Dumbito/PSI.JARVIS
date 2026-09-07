from __future__ import annotations

import sys
from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QComboBox, QDialog, QDialogButtonBox, QFrame, QGridLayout,
    QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMainWindow,
    QProgressBar, QPushButton, QStackedWidget, QStatusBar, QTableWidget,
    QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget,
)

from psi_jarvis.gui.data import GuiDataService
from psi_jarvis.gui.theme import apply_theme

NAV_ITEMS = (
    ("Dashboard", "⌂"), ("Projects", "▣"), ("Papers", "▤"),
    ("Sources", "⇄"), ("Screening", "✓"), ("Analysis", "◫"),
    ("Reports", "▥"), ("Audit", "◇"), ("Settings", "⚙"),
)


def page_header(title: str, subtitle: str) -> QVBoxLayout:
    layout = QVBoxLayout(); layout.setSpacing(4)
    heading = QLabel(title); heading.setObjectName("pageTitle")
    sub = QLabel(subtitle); sub.setObjectName("pageSubtitle")
    layout.addWidget(heading); layout.addWidget(sub)
    return layout


def card(title: str | None = None) -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame(); frame.setObjectName("card")
    layout = QVBoxLayout(frame); layout.setContentsMargins(16, 14, 16, 14); layout.setSpacing(9)
    if title:
        label = QLabel(title); label.setObjectName("sectionTitle"); layout.addWidget(label)
    return frame, layout


def metric(label: str, value: int, accent: str) -> QFrame:
    frame, layout = card()
    value_label = QLabel(f"{value:,}"); value_label.setObjectName("metricValue")
    label_label = QLabel(label); label_label.setObjectName("metricLabel")
    accent_label = QLabel(accent); accent_label.setObjectName("metricAccent")
    layout.addWidget(value_label); layout.addWidget(label_label); layout.addWidget(accent_label)
    return frame


class PaperDialog(QDialog):
    def __init__(self, details: dict, parent: QWidget | None = None) -> None:
        super().__init__(parent); self.setWindowTitle("Paper details"); self.resize(760, 600)
        layout = QVBoxLayout(self)
        title = QLabel(details["title"]); title.setObjectName("dialogTitle"); title.setWordWrap(True); layout.addWidget(title)
        metadata, metadata_layout = card()
        metadata_layout.addWidget(QLabel(f"Authors: {details['authors'] or '—'}"))
        metadata_layout.addWidget(QLabel(f"Journal: {details['journal'] or '—'} · Year: {details['year'] or '—'}"))
        metadata_layout.addWidget(QLabel(f"DOI: {details['doi'] or '—'} · PMID: {details['pmid'] or '—'}"))
        metadata_layout.addWidget(QLabel(f"Provenance records: {details['provenance_count']}")); layout.addWidget(metadata)
        abstract = QTextEdit(); abstract.setReadOnly(True); abstract.setPlainText(details["abstract"] or "No abstract stored."); layout.addWidget(abstract, 1)
        buttons = QDialogButtonBox(QDialogButtonBox.Close); buttons.rejected.connect(self.reject); layout.addWidget(buttons)


class DashboardPage(QWidget):
    def __init__(self, data: GuiDataService, refresh: Callable[[], None]) -> None:
        super().__init__(); self.data = data; self.refresh = refresh
        self.root = QVBoxLayout(self); self.root.setContentsMargins(28, 24, 28, 28); self.root.setSpacing(14); self.rebuild()

    def rebuild(self) -> None:
        while self.root.count():
            item = self.root.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        heading = QHBoxLayout(); title = QLabel("Research workspace"); title.setObjectName("pageTitle"); heading.addWidget(title); heading.addStretch()
        refresh = QPushButton("Refresh"); refresh.setObjectName("secondary"); refresh.clicked.connect(self.refresh); heading.addWidget(refresh)
        self.root.addLayout(heading); self.root.addWidget(QLabel("A reproducible workspace for scientific paper acquisition, screening and provenance."))
        snap = self.data.snapshot(); grid = QGridLayout(); grid.setSpacing(12)
        metrics = (("Projects", snap.projects, "Review workspaces"), ("Papers", snap.papers, "Persisted corpus"), ("Screened", snap.screened, "Recorded results"), ("Pending", snap.pending, "Awaiting screening"), ("Included", snap.included, "Accepted"), ("Excluded", snap.excluded, "Rejected"))
        for i, values in enumerate(metrics): grid.addWidget(metric(*values), i // 3, i % 3)
        self.root.addLayout(grid)
        lower = QGridLayout(); lower.setSpacing(12)
        progress, progress_layout = card("Screening progress"); percent = int(snap.screened / snap.papers * 100) if snap.papers else 0
        bar = QProgressBar(); bar.setValue(percent); bar.setFormat(f"{percent}%"); progress_layout.addWidget(bar); progress_layout.addWidget(QLabel(f"{snap.screened:,} of {snap.papers:,} papers have persisted screening results.")); lower.addWidget(progress, 0, 0)
        sources, source_layout = card("Acquisition footprint")
        if snap.source_counts:
            for source, count in snap.source_counts: source_layout.addWidget(QLabel(f"{source.upper()}  ·  {count:,} acquisition batch(es)"))
        else: source_layout.addWidget(QLabel("No acquisition batches recorded."))
        lower.addWidget(sources, 0, 1)
        boundary, boundary_layout = card("Methodological boundary")
        boundary_layout.addWidget(QLabel("Authority: deterministic ScreeningEngine")); boundary_layout.addWidget(QLabel("Provenance: retained across acquisition and synchronization")); boundary_layout.addWidget(QLabel("AI/NLP: auxiliary only; never silently changes scientific decisions")); lower.addWidget(boundary, 1, 0, 1, 2)
        self.root.addLayout(lower); self.root.addStretch()


class ProjectsPage(QWidget):
    def __init__(self, data: GuiDataService) -> None:
        super().__init__(); root = QVBoxLayout(self); root.setContentsMargins(28,24,28,28); root.setSpacing(14); root.addLayout(page_header("Projects", "Review protocols persisted in the project repository."))
        table = QTableWidget(0, 4); table.setHorizontalHeaderLabels(["Project", "Topic", "Research question", "Created"]); table.horizontalHeader().setStretchLastSection(True); table.setSelectionBehavior(QTableWidget.SelectRows)
        for row, project in enumerate(data.projects()):
            table.insertRow(row)
            for col, value in enumerate((project.name, project.criteria.topic, project.research_question, project.created_at.isoformat())): table.setItem(row, col, QTableWidgetItem(str(value)))
        root.addWidget(table, 1); note = QLabel("Project editing remains outside this presentation layer; protocol semantics stay in the application/domain layer."); note.setObjectName("pageSubtitle"); root.addWidget(note)


class PapersPage(QWidget):
    def __init__(self, data: GuiDataService) -> None:
        super().__init__(); self.data = data; root = QVBoxLayout(self); root.setContentsMargins(28,24,28,28); root.setSpacing(12)
        top = QHBoxLayout(); title = QLabel("Papers"); title.setObjectName("pageTitle"); top.addWidget(title); top.addStretch(); self.search = QLineEdit(); self.search.setPlaceholderText("Search title, DOI, PMID, journal…"); self.search.setMaximumWidth(360); top.addWidget(self.search); root.addLayout(top)
        self.table = QTableWidget(0, 5); self.table.setHorizontalHeaderLabels(["Title","Year","Journal","DOI","PMID"]); self.table.horizontalHeader().setStretchLastSection(True); self.table.setSelectionBehavior(QTableWidget.SelectRows); self.table.setEditTriggers(QTableWidget.NoEditTriggers); self.table.doubleClicked.connect(self.open_selected); self.search.textChanged.connect(self.filter_rows); root.addWidget(self.table,1)
        self.rows = data.papers(); self.populate(); hint = QLabel("Double-click a paper to inspect its stored metadata and provenance count."); hint.setObjectName("pageSubtitle"); root.addWidget(hint)

    def populate(self) -> None:
        self.table.setRowCount(len(self.rows))
        for row, paper in enumerate(self.rows):
            for col, value in enumerate((paper.title, paper.publication_year or "—", paper.journal or "—", paper.doi or "—", paper.pmid or "—")): self.table.setItem(row, col, QTableWidgetItem(str(value)))
            self.table.item(row, 0).setData(Qt.UserRole, str(paper.id))

    def filter_rows(self, text: str) -> None:
        query = text.casefold().strip()
        for row in range(self.table.rowCount()):
            haystack = " ".join(self.table.item(row, col).text() for col in range(self.table.columnCount())).casefold(); self.table.setRowHidden(row, query not in haystack)

    def open_selected(self) -> None:
        row = self.table.currentRow()
        if row < 0: return
        paper_id = self.table.item(row, 0).data(Qt.UserRole); details = self.data.paper_details(paper_id)
        if details: PaperDialog(details, self).exec()


class SourcesPage(QWidget):
    def __init__(self, data: GuiDataService) -> None:
        super().__init__(); self.data = data; root = QVBoxLayout(self); root.setContentsMargins(28,24,28,28); root.setSpacing(12)
        top = QHBoxLayout(); top.addLayout(page_header("Sources", "Connection visibility for bibliographic acquisition.")); top.addStretch(); refresh = QPushButton("Refresh sources"); refresh.setObjectName("secondary"); refresh.clicked.connect(self.rebuild); top.addWidget(refresh); root.addLayout(top)
        self.list = QListWidget(); self.list.setSpacing(6); root.addWidget(self.list,1); self.rebuild()

    def rebuild(self) -> None:
        self.list.clear()
        for source in self.data.sources():
            item = QListWidgetItem(f"{source.display_name}    ·    {source.status.upper()}" + (f"    ·    {source.detail}" if source.detail else "")); item.setToolTip(f"Source key: {source.key}\nStatus: {source.status}\n{source.detail}"); self.list.addItem(item)


class ScreeningPage(QWidget):
    def __init__(self, data: GuiDataService) -> None:
        super().__init__(); self.data = data; root = QVBoxLayout(self); root.setContentsMargins(28,24,28,28); root.setSpacing(12)
        top = QHBoxLayout(); title = QLabel("Screening"); title.setObjectName("pageTitle"); top.addWidget(title); top.addStretch(); self.filter = QComboBox(); self.filter.addItems(["All decisions","Included","Excluded"]); self.filter.currentTextChanged.connect(self.apply_filter); top.addWidget(self.filter); root.addLayout(top)
        root.addWidget(QLabel("Persisted screening results are displayed as evidence. The GUI does not create or alter scientific decisions.")); self.table = QTableWidget(0,5); self.table.setHorizontalHeaderLabels(["Paper","Year","Decision","Reason","Criteria version"]); self.table.horizontalHeader().setStretchLastSection(True); self.table.setEditTriggers(QTableWidget.NoEditTriggers); root.addWidget(self.table,1); self.rows = data.screening_rows(); self.populate()

    def populate(self) -> None:
        self.table.setRowCount(len(self.rows))
        for row, result in enumerate(self.rows):
            for col, value in enumerate((result.title, result.year or "—", result.decision, result.reason, result.criteria_version or "—")): self.table.setItem(row,col,QTableWidgetItem(str(value)))
        self.apply_filter(self.filter.currentText())

    def apply_filter(self, value: str) -> None:
        for row in range(self.table.rowCount()): self.table.setRowHidden(row, value != "All decisions" and self.table.item(row,2).text() != value)


class AnalysisPage(QWidget):
    def __init__(self, data: GuiDataService) -> None:
        super().__init__(); self.data = data; self.root = QVBoxLayout(self); self.root.setContentsMargins(28,24,28,28); self.root.setSpacing(14); self.rebuild()

    def rebuild(self) -> None:
        while self.root.count():
            item = self.root.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        self.root.addLayout(page_header("Analysis", "Read-only analytical views derived from persisted corpus state."))
        quality = self.data.metadata_quality(); total = quality.total_papers
        frame, layout = card("Metadata quality")
        for label, count in (("Abstract", quality.with_abstract), ("Authors", quality.with_authors), ("DOI", quality.with_doi), ("PMID", quality.with_pmid), ("Journal", quality.with_journal), ("Publication year", quality.with_year)):
            rate = int(count / total * 100) if total else 0; layout.addWidget(QLabel(f"{label}: {count:,}/{total:,} · {rate}% complete"))
        self.root.addWidget(frame)
        snap = self.data.snapshot(); decisions, decision_layout = card("Decision distribution"); decision_layout.addWidget(QLabel(f"Included: {snap.included:,}")); decision_layout.addWidget(QLabel(f"Excluded: {snap.excluded:,}")); decision_layout.addWidget(QLabel(f"Screened: {snap.screened:,}")); self.root.addWidget(decisions)
        runs, runs_layout = card("Persisted screening runs"); snapshots = self.data.screening_runs()
        if snapshots:
            for run in snapshots[:8]: runs_layout.addWidget(QLabel(f"{run.started_at} · {run.criteria_version} · {run.screened_papers:,} screened · {run.duplicates_removed:,} duplicates removed"))
        else: runs_layout.addWidget(QLabel("No persisted screening runs recorded."))
        self.root.addWidget(runs); self.root.addStretch()


class ReportsPage(QWidget):
    def __init__(self, data: GuiDataService) -> None:
        super().__init__(); root = QVBoxLayout(self); root.setContentsMargins(28,24,28,28); root.setSpacing(14); root.addLayout(page_header("Reports", "Reproducible reporting backed by the existing application reporting layer."))
        frame, layout = card("Persisted screening runs available as report provenance"); runs = data.screening_runs()
        if runs:
            for run in runs: layout.addWidget(QLabel(f"{run.started_at} · {run.criteria_version} · input {run.total_input:,} · unique {run.unique_papers:,} · screened {run.screened_papers:,}"))
        else: layout.addWidget(QLabel("No persisted screening runs recorded yet."))
        root.addWidget(frame); root.addWidget(QLabel("Report rendering/export remains owned by ReportBuilder, renderers and ReportPackageBuilder. The GUI does not reimplement reporting logic or silently rerun screening.")); root.addStretch()


class AuditPage(QWidget):
    def __init__(self, data: GuiDataService) -> None:
        super().__init__(); self.data = data; root = QVBoxLayout(self); root.setContentsMargins(28,24,28,28); root.setSpacing(12); top = QHBoxLayout(); top.addLayout(page_header("Audit", "Metadata-change history and provenance evidence.")); top.addStretch(); refresh = QPushButton("Refresh"); refresh.setObjectName("secondary"); refresh.clicked.connect(self.populate); top.addWidget(refresh); root.addLayout(top); self.table = QTableWidget(0,4); self.table.setHorizontalHeaderLabels(["Changed at","Paper ID","Source","Changed fields"]); self.table.horizontalHeader().setStretchLastSection(True); self.table.setEditTriggers(QTableWidget.NoEditTriggers); root.addWidget(self.table,1); self.populate()

    def populate(self) -> None:
        rows = self.data.audit_rows(); self.table.setRowCount(len(rows))
        for row, audit in enumerate(rows):
            for col, value in enumerate((audit.changed_at, audit.paper_id, audit.source_key, ", ".join(audit.changed_fields))): self.table.setItem(row,col,QTableWidgetItem(value))


class SettingsPage(QWidget):
    def __init__(self, data: GuiDataService) -> None:
        super().__init__(); root = QVBoxLayout(self); root.setContentsMargins(28,24,28,28); root.setSpacing(14); root.addLayout(page_header("Settings", "Runtime paths and methodological safeguards."))
        db, db_layout = card("Database"); db_layout.addWidget(QLabel(str(data.database_path))); db_layout.addWidget(QLabel("Override with PSI_JARVIS_DATABASE_PATH when launching the application.")); root.addWidget(db)
        boundary, boundary_layout = card("Scientific safeguards"); boundary_layout.addWidget(QLabel("Deterministic screening remains authoritative.")); boundary_layout.addWidget(QLabel("Synchronization never resolves metadata conflicts silently.")); boundary_layout.addWidget(QLabel("Credentials and tokens are kept outside the source tree.")); root.addWidget(boundary); root.addStretch()


class MainWindow(QMainWindow):
    def __init__(self, data_service: GuiDataService | None = None) -> None:
        super().__init__(); self.setWindowTitle("PSI.JARVIS V.1"); self.resize(1440,900); self.setMinimumSize(1100,700); self.data = data_service or GuiDataService(); self.pages = QStackedWidget(); self.nav_buttons: list[QPushButton] = []; self._build_ui(); self.statusBar().showMessage("Ready · deterministic scientific workspace")

    def _build_ui(self) -> None:
        root = QWidget(); root_layout = QHBoxLayout(root); root_layout.setContentsMargins(0,0,0,0); root_layout.setSpacing(0)
        sidebar = QFrame(); sidebar.setObjectName("sidebar"); sidebar.setFixedWidth(220); side = QVBoxLayout(sidebar); side.setContentsMargins(14,20,14,14); side.setSpacing(4)
        brand = QHBoxLayout(); brand_label = QLabel("PSI.JARVIS"); brand_label.setObjectName("brand"); version = QLabel("V.1"); version.setObjectName("version"); brand.addWidget(brand_label); brand.addWidget(version); brand.addStretch(); side.addLayout(brand)
        tagline = QLabel("Scientific Paper Screening\n& Analysis System"); tagline.setObjectName("tagline"); side.addWidget(tagline); side.addSpacing(16)
        for index, (label, icon) in enumerate(NAV_ITEMS):
            button = QPushButton(f"  {icon}   {label}"); button.setObjectName("nav"); button.setProperty("active", index == 0); button.clicked.connect(lambda checked=False, i=index: self._select_page(i)); self.nav_buttons.append(button); side.addWidget(button)
        side.addStretch(); footer = QLabel("Human methodological authority\n\nDeterministic · Traceable\nReproducible"); footer.setObjectName("tagline"); side.addWidget(footer); root_layout.addWidget(sidebar)
        content = QWidget(); content_layout = QVBoxLayout(content); content_layout.setContentsMargins(0,0,0,0)
        for page in (DashboardPage(self.data, self.refresh_dashboard), ProjectsPage(self.data), PapersPage(self.data), SourcesPage(self.data), ScreeningPage(self.data), AnalysisPage(self.data), ReportsPage(self.data), AuditPage(self.data), SettingsPage(self.data)): self.pages.addWidget(page)
        content_layout.addWidget(self.pages); root_layout.addWidget(content,1); self.setCentralWidget(root); self.setStatusBar(QStatusBar())

    def _select_page(self, index: int) -> None:
        self.pages.setCurrentIndex(index)
        for i, button in enumerate(self.nav_buttons): button.setProperty("active", i == index); button.style().unpolish(button); button.style().polish(button)
        self.statusBar().showMessage(f"{NAV_ITEMS[index][0]} · ready")

    def refresh_dashboard(self) -> None:
        old = self.pages.widget(0); self.pages.removeWidget(old); old.deleteLater(); self.pages.insertWidget(0, DashboardPage(self.data, self.refresh_dashboard)); self._select_page(0); self.statusBar().showMessage("Dashboard refreshed")


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv); apply_theme(app); window = MainWindow(); window.show(); return app.exec()
