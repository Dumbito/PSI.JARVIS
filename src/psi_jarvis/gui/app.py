from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable
from uuid import UUID

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFrame,
    QGridLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMainWindow, QMessageBox, QProgressBar, QPushButton, QStackedWidget,
    QStatusBar, QTableWidget, QTableWidgetItem, QTabWidget, QTextEdit,
    QVBoxLayout, QWidget,
)

from psi_jarvis.gui.data import GuiDataService
from psi_jarvis.gui.theme import apply_theme
from psi_jarvis.gui.workflow import GuiWorkflowService, UnsupportedFileFormat

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


def rate_table(headers: list[str], rows: list[tuple]) -> QTableWidget:
    table = QTableWidget(len(rows), len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.horizontalHeader().setStretchLastSection(True)
    table.setEditTriggers(QTableWidget.NoEditTriggers)
    table.setSelectionBehavior(QTableWidget.SelectRows)
    for row, values in enumerate(rows):
        for col, value in enumerate(values):
            table.setItem(row, col, QTableWidgetItem(str(value)))
    return table


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


class NewProjectDialog(QDialog):
    """Creates a ReviewProject through CreateReviewProjectService — no domain logic here."""

    def __init__(self, workflow: GuiWorkflowService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.workflow = workflow
        self.setWindowTitle("New review project")
        self.resize(520, 460)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Project name")); self.name = QLineEdit(); layout.addWidget(self.name)
        layout.addWidget(QLabel("Research question")); self.question = QLineEdit(); layout.addWidget(self.question)
        layout.addWidget(QLabel("Topic (required)")); self.topic = QLineEdit(); layout.addWidget(self.topic)
        layout.addWidget(QLabel("Inclusion rules (one per line)"))
        self.inclusion = QTextEdit(); self.inclusion.setFixedHeight(90); layout.addWidget(self.inclusion)
        layout.addWidget(QLabel("Exclusion rules (one per line)"))
        self.exclusion = QTextEdit(); self.exclusion.setFixedHeight(90); layout.addWidget(self.exclusion)
        self.error = QLabel(""); self.error.setObjectName("pageSubtitle"); self.error.setWordWrap(True); layout.addWidget(self.error)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._create); buttons.rejected.connect(self.reject); layout.addWidget(buttons)
        self.created_project = None

    @staticmethod
    def _lines(widget: QTextEdit) -> tuple[str, ...]:
        return tuple(line.strip() for line in widget.toPlainText().splitlines() if line.strip())

    def _create(self) -> None:
        try:
            self.created_project = self.workflow.create_project(
                name=self.name.text(),
                research_question=self.question.text(),
                topic=self.topic.text(),
                inclusion=self._lines(self.inclusion),
                exclusion=self._lines(self.exclusion),
            )
            self.accept()
        except Exception as exc:
            self.error.setText(str(exc))


class ImportScreenDialog(QDialog):
    """Runs AcquisitionService + ScreenReviewProjectService against an existing project."""

    def __init__(self, workflow: GuiWorkflowService, projects, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.workflow = workflow
        self.projects = list(projects)
        self.setWindowTitle("Import & screen")
        self.resize(560, 260)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Review project"))
        self.project_box = QComboBox()
        for project in self.projects:
            self.project_box.addItem(f"{project.name}  ·  {project.criteria.topic}", str(project.project_id))
        layout.addWidget(self.project_box)
        layout.addWidget(QLabel("Source file (.csv, .xlsx, .ris)"))
        file_row = QHBoxLayout()
        self.path_field = QLineEdit(); self.path_field.setReadOnly(True); file_row.addWidget(self.path_field, 1)
        browse = QPushButton("Browse…"); browse.setObjectName("secondary"); browse.clicked.connect(self._browse); file_row.addWidget(browse)
        layout.addLayout(file_row)
        self.error = QLabel(""); self.error.setObjectName("pageSubtitle"); self.error.setWordWrap(True); layout.addWidget(self.error)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._run); buttons.rejected.connect(self.reject); layout.addWidget(buttons)
        self.outcome = None

    def _browse(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select corpus file", str(Path.home()), "Corpus files (*.csv *.xlsx *.xls *.ris)")
        if path:
            self.path_field.setText(path)

    def _run(self) -> None:
        if not self.projects:
            self.error.setText("Create a review project first."); return
        if not self.path_field.text():
            self.error.setText("Choose a file to import."); return
        project_id = UUID(self.project_box.currentData())
        try:
            self.outcome = self.workflow.import_and_screen(project_id, self.path_field.text())
            self.accept()
        except UnsupportedFileFormat as exc:
            self.error.setText(str(exc))
        except Exception as exc:
            self.error.setText(str(exc))


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
    def __init__(self, data: GuiDataService, workflow: GuiWorkflowService, refresh_all: Callable[[], None]) -> None:
        super().__init__(); self.data = data; self.workflow = workflow; self.refresh_all = refresh_all
        root = QVBoxLayout(self); root.setContentsMargins(28, 24, 28, 28); root.setSpacing(14)
        top = QHBoxLayout(); top.addLayout(page_header("Projects", "Review protocols persisted in the project repository.")); top.addStretch()
        new_project = QPushButton("New project"); new_project.clicked.connect(self._new_project); top.addWidget(new_project)
        root.addLayout(top)
        self.table = QTableWidget(0, 4); self.table.setHorizontalHeaderLabels(["Project", "Topic", "Research question", "Created"]); self.table.horizontalHeader().setStretchLastSection(True); self.table.setSelectionBehavior(QTableWidget.SelectRows); self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        root.addWidget(self.table, 1)
        note = QLabel("Project editing remains outside this presentation layer; protocol semantics stay in the application/domain layer.")
        note.setObjectName("pageSubtitle"); root.addWidget(note)
        self.populate()

    def populate(self) -> None:
        projects = self.data.projects()
        self.table.setRowCount(len(projects))
        for row, project in enumerate(projects):
            for col, value in enumerate((project.name, project.criteria.topic, project.research_question, project.created_at.isoformat())):
                self.table.setItem(row, col, QTableWidgetItem(str(value)))

    def _new_project(self) -> None:
        dialog = NewProjectDialog(self.workflow, self)
        if dialog.exec() == QDialog.Accepted and dialog.created_project is not None:
            self.refresh_all()


class PapersPage(QWidget):
    def __init__(self, data: GuiDataService, workflow: GuiWorkflowService, refresh_all: Callable[[], None]) -> None:
        super().__init__(); self.data = data; self.workflow = workflow; self.refresh_all = refresh_all
        root = QVBoxLayout(self); root.setContentsMargins(28, 24, 28, 28); root.setSpacing(12)
        top = QHBoxLayout(); title = QLabel("Papers"); title.setObjectName("pageTitle"); top.addWidget(title); top.addStretch()
        self.search = QLineEdit(); self.search.setPlaceholderText("Search title, DOI, PMID, journal…"); self.search.setMaximumWidth(320); top.addWidget(self.search)
        import_button = QPushButton("Import & screen…"); import_button.clicked.connect(self._import_and_screen); top.addWidget(import_button)
        root.addLayout(top)
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

    def _import_and_screen(self) -> None:
        projects = self.data.projects()
        dialog = ImportScreenDialog(self.workflow, projects, self)
        if dialog.exec() == QDialog.Accepted and dialog.outcome is not None:
            outcome = dialog.outcome
            QMessageBox.information(
                self, "Import & screen complete",
                f"Input: {outcome.total_input}\nUnique: {outcome.unique_papers}\n"
                f"Duplicates removed: {outcome.duplicates_removed}\nScreened: {outcome.screened_papers}\n"
                f"Included: {outcome.included}  ·  Excluded: {outcome.excluded}\n\nRun ID: {outcome.run_id}",
            )
            self.refresh_all()


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
    """Read-only analytical views, one tab per domain analysis class."""

    def __init__(self, data: GuiDataService) -> None:
        super().__init__(); self.data = data
        root = QVBoxLayout(self); root.setContentsMargins(28, 24, 28, 28); root.setSpacing(14)
        root.addLayout(page_header("Analysis", "Read-only analytical views derived from persisted corpus state."))
        self.tabs = QTabWidget()
        self.tabs.addTab(self._overview_tab(), "Overview")
        self.tabs.addTab(self._rules_tab(), "Rules")
        self.tabs.addTab(self._exclusions_tab(), "Exclusions")
        self.tabs.addTab(self._deduplication_tab(), "Deduplication")
        self.tabs.addTab(self._authors_tab(), "Authors")
        self.tabs.addTab(self._journals_tab(), "Journals")
        self.tabs.addTab(self._years_tab(), "Years")
        root.addWidget(self.tabs, 1)

    def _overview_tab(self) -> QWidget:
        page = QWidget(); layout = QVBoxLayout(page); layout.setSpacing(14)
        quality = self.data.metadata_quality(); total = quality.total_papers
        frame, quality_layout = card("Metadata quality")
        for label, count in (("Abstract", quality.with_abstract), ("Authors", quality.with_authors), ("DOI", quality.with_doi), ("PMID", quality.with_pmid), ("Journal", quality.with_journal), ("Publication year", quality.with_year)):
            rate = int(count / total * 100) if total else 0; quality_layout.addWidget(QLabel(f"{label}: {count:,}/{total:,} · {rate}% complete"))
        layout.addWidget(frame)
        snap = self.data.snapshot(); decisions, decision_layout = card("Decision distribution"); decision_layout.addWidget(QLabel(f"Included: {snap.included:,}")); decision_layout.addWidget(QLabel(f"Excluded: {snap.excluded:,}")); decision_layout.addWidget(QLabel(f"Screened: {snap.screened:,}")); layout.addWidget(decisions)
        runs, runs_layout = card("Persisted screening runs"); snapshots = self.data.screening_runs()
        if snapshots:
            for run in snapshots[:8]: runs_layout.addWidget(QLabel(f"{run.started_at} · {run.criteria_version} · {run.screened_papers:,} screened · {run.duplicates_removed:,} duplicates removed"))
        else: runs_layout.addWidget(QLabel("No persisted screening runs recorded."))
        layout.addWidget(runs); layout.addStretch()
        return page

    def _rules_tab(self) -> QWidget:
        page = QWidget(); layout = QVBoxLayout(page)
        layout.addWidget(QLabel("Matched/failed counts per rule ID, aggregated across every persisted audit."))
        analysis = self.data.rule_analysis()
        rows = [(rule.rule_id, rule.matched, rule.failed, f"{rule.match_rate:.0%}") for rule in analysis.rules]
        layout.addWidget(rate_table(["Rule ID", "Matched", "Failed", "Match rate"], rows))
        if not rows: layout.addWidget(QLabel("No rule evidence recorded yet."))
        return page

    def _exclusions_tab(self) -> QWidget:
        page = QWidget(); layout = QVBoxLayout(page)
        layout.addWidget(QLabel("Distribution of exclusion reasons across every persisted audit."))
        analysis = self.data.exclusion_reason_analysis()
        rows = [(reason.reason, reason.count, f"{reason.rate:.0%}") for reason in analysis.reasons]
        layout.addWidget(rate_table(["Reason", "Count", "Share of exclusions"], rows))
        if not rows: layout.addWidget(QLabel("No excluded papers recorded yet."))
        return page

    def _deduplication_tab(self) -> QWidget:
        page = QWidget(); layout = QVBoxLayout(page)
        analysis = self.data.deduplication_analysis()
        frame, frame_layout = card("Deduplication (all persisted runs)")
        frame_layout.addWidget(QLabel(f"Total input: {analysis.total_input:,}"))
        frame_layout.addWidget(QLabel(f"Unique papers: {analysis.unique_papers:,}"))
        frame_layout.addWidget(QLabel(f"Duplicates removed: {analysis.duplicate_papers:,}"))
        frame_layout.addWidget(QLabel(f"Duplicate rate: {analysis.duplicate_rate:.0%}"))
        layout.addWidget(frame); layout.addStretch()
        return page

    def _authors_tab(self) -> QWidget:
        page = QWidget(); layout = QVBoxLayout(page)
        analysis = self.data.author_analysis()
        layout.addWidget(QLabel(f"{analysis.unique_authors:,} unique authors across {analysis.total_papers:,} papers · {analysis.author_coverage_rate:.0%} coverage."))
        rows = sorted(analysis.by_author, key=lambda item: -item[1])[:50]
        layout.addWidget(rate_table(["Author", "Papers"], rows))
        return page

    def _journals_tab(self) -> QWidget:
        page = QWidget(); layout = QVBoxLayout(page)
        analysis = self.data.journal_analysis()
        layout.addWidget(QLabel(f"{analysis.unique_journals:,} unique journals across {analysis.total_papers:,} papers · {analysis.journal_coverage_rate:.0%} coverage."))
        rows = sorted(analysis.by_journal, key=lambda item: -item[1])[:50]
        layout.addWidget(rate_table(["Journal", "Papers"], rows))
        return page

    def _years_tab(self) -> QWidget:
        page = QWidget(); layout = QVBoxLayout(page)
        analysis = self.data.publication_year_analysis()
        span = f"{analysis.year_min}–{analysis.year_max}" if analysis.year_min else "—"
        layout.addWidget(QLabel(f"Span: {span} · {analysis.year_coverage_rate:.0%} of papers carry a publication year."))
        rows = sorted(analysis.by_year)
        layout.addWidget(rate_table(["Year", "Papers"], rows))
        return page


class ReportsPage(QWidget):
    def __init__(self, data: GuiDataService, workflow: GuiWorkflowService) -> None:
        super().__init__(); self.data = data; self.workflow = workflow
        root = QVBoxLayout(self); root.setContentsMargins(28,24,28,28); root.setSpacing(14)
        root.addLayout(page_header("Reports", "Reproducible reporting backed by the existing application reporting layer."))
        top = QHBoxLayout()
        self.run_box = QComboBox()
        self.runs = self.data.screening_runs()
        for run in self.runs:
            self.run_box.addItem(f"{run.started_at} · {run.criteria_version} · {run.screened_papers:,} screened", run.run_id)
        top.addWidget(self.run_box, 1)
        export = QPushButton("Export report…"); export.clicked.connect(self._export); top.addWidget(export)
        root.addLayout(top)
        frame, layout = card("Persisted screening runs available as report provenance")
        if self.runs:
            for run in self.runs: layout.addWidget(QLabel(f"{run.started_at} · {run.criteria_version} · input {run.total_input:,} · unique {run.unique_papers:,} · screened {run.screened_papers:,}"))
        else: layout.addWidget(QLabel("No persisted screening runs recorded yet."))
        root.addWidget(frame); root.addWidget(QLabel("Report content is produced by existing domain analysis classes and rendered/exported by the existing JSON/Markdown renderers and ReportExporter. The GUI does not reimplement reporting logic or silently rerun screening.")); root.addStretch()

    def _export(self) -> None:
        if not self.runs:
            QMessageBox.warning(self, "No runs", "There are no persisted screening runs to export yet."); return
        run_id = UUID(self.run_box.currentData())
        directory = QFileDialog.getExistingDirectory(self, "Choose export folder", str(Path.home()))
        if not directory: return
        try:
            paths = self.workflow.export_report(run_id, directory)
        except Exception as exc:
            QMessageBox.critical(self, "Export failed", str(exc)); return
        if paths is None:
            QMessageBox.warning(self, "Nothing to export", "No audit evidence was found for the selected run."); return
        json_path, markdown_path = paths
        QMessageBox.information(self, "Report exported", f"JSON: {json_path}\nMarkdown: {markdown_path}")


class AuditPage(QWidget):
    def __init__(self, data: GuiDataService) -> None:
        super().__init__(); self.data = data; root = QVBoxLayout(self); root.setContentsMargins(28,24,28,28); root.setSpacing(12)
        top = QHBoxLayout(); top.addLayout(page_header("Audit", "Metadata-change history and provenance evidence.")); top.addStretch(); refresh = QPushButton("Refresh"); refresh.setObjectName("secondary"); refresh.clicked.connect(self.populate); top.addWidget(refresh); root.addLayout(top)
        self.table = QTableWidget(0,4); self.table.setHorizontalHeaderLabels(["Changed at","Paper ID","Source","Changed fields"]); self.table.horizontalHeader().setStretchLastSection(True); self.table.setEditTriggers(QTableWidget.NoEditTriggers); root.addWidget(self.table,1); self.populate()

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
        super().__init__(); self.setWindowTitle("PSI.JARVIS V.1"); self.resize(1440,900); self.setMinimumSize(1100,700)
        self.data = data_service or GuiDataService()
        self.workflow = GuiWorkflowService(self.data.database_path)
        self.pages = QStackedWidget(); self.nav_buttons: list[QPushButton] = []; self._build_ui(); self.statusBar().showMessage("Ready · deterministic scientific workspace")

    def _build_ui(self) -> None:
        root = QWidget(); root_layout = QHBoxLayout(root); root_layout.setContentsMargins(0,0,0,0); root_layout.setSpacing(0)
        sidebar = QFrame(); sidebar.setObjectName("sidebar"); sidebar.setFixedWidth(220); side = QVBoxLayout(sidebar); side.setContentsMargins(14,20,14,14); side.setSpacing(4)
        brand = QHBoxLayout(); brand_label = QLabel("PSI.JARVIS"); brand_label.setObjectName("brand"); version = QLabel("V.1"); version.setObjectName("version"); brand.addWidget(brand_label); brand.addWidget(version); brand.addStretch(); side.addLayout(brand)
        tagline = QLabel("Scientific Paper Screening\n& Analysis System"); tagline.setObjectName("tagline"); side.addWidget(tagline); side.addSpacing(16)
        for index, (label, icon) in enumerate(NAV_ITEMS):
            button = QPushButton(f"  {icon}   {label}"); button.setObjectName("nav"); button.setProperty("active", index == 0); button.clicked.connect(lambda checked=False, i=index: self._select_page(i)); self.nav_buttons.append(button); side.addWidget(button)
        side.addStretch(); footer = QLabel("Human methodological authority\n\nDeterministic · Traceable\nReproducible"); footer.setObjectName("tagline"); side.addWidget(footer); root_layout.addWidget(sidebar)
        content = QWidget(); content_layout = QVBoxLayout(content); content_layout.setContentsMargins(0,0,0,0); content_layout.addWidget(self.pages); root_layout.addWidget(content,1); self.setCentralWidget(root); self.setStatusBar(QStatusBar())
        self._build_pages()

    def _build_pages(self) -> None:
        while self.pages.count():
            widget = self.pages.widget(0); self.pages.removeWidget(widget); widget.deleteLater()
        pages = (
            DashboardPage(self.data, self.refresh_all),
            ProjectsPage(self.data, self.workflow, self.refresh_all),
            PapersPage(self.data, self.workflow, self.refresh_all),
            SourcesPage(self.data),
            ScreeningPage(self.data),
            AnalysisPage(self.data),
            ReportsPage(self.data, self.workflow),
            AuditPage(self.data),
            SettingsPage(self.data),
        )
        for page in pages: self.pages.addWidget(page)

    def _select_page(self, index: int) -> None:
        self.pages.setCurrentIndex(index)
        for i, button in enumerate(self.nav_buttons): button.setProperty("active", i == index); button.style().unpolish(button); button.style().polish(button)
        self.statusBar().showMessage(f"{NAV_ITEMS[index][0]} · ready")

    def refresh_all(self) -> None:
        current = self.pages.currentIndex()
        self._build_pages()
        self._select_page(max(0, current))
        self.statusBar().showMessage("Workspace refreshed")


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv); apply_theme(app)
    window = MainWindow()
    window.show()
    return app.exec()
