from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path
from uuid import UUID

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from psi_jarvis.gui.audit_explorer import AuditExplorerView
from psi_jarvis.gui.command_palette import Command, CommandPalette
from psi_jarvis.gui.data import GuiDataService
from psi_jarvis.gui.formatting import format_timestamp, format_timestamp_str
from psi_jarvis.gui.nav_icons import nav_icon
from psi_jarvis.gui.progress_ring import ProgressRing
from psi_jarvis.gui.project_workspace import ProjectWorkspaceView
from psi_jarvis.gui.theme import apply_theme
from psi_jarvis.gui.tutorial import TutorialDialog
from psi_jarvis.gui.workflow import GuiWorkflowService, UnsupportedFileFormat

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


def page_header(title: str, subtitle: str) -> QVBoxLayout:
    layout = QVBoxLayout()
    layout.setSpacing(4)
    heading = QLabel(title)
    heading.setObjectName("pageTitle")
    sub = QLabel(subtitle)
    sub.setObjectName("pageSubtitle")
    layout.addWidget(heading)
    layout.addWidget(sub)
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
    layout.addWidget(value_label)
    metric_label = QLabel(label)
    metric_label.setObjectName("metricLabel")
    layout.addWidget(metric_label)
    accent_label = QLabel(accent)
    accent_label.setObjectName("metricAccent")
    layout.addWidget(accent_label)
    return frame


def rate_table(headers: list[str], rows: list[tuple]) -> QTableWidget:
    table = QTableWidget(len(rows), len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.horizontalHeader().setStretchLastSection(True)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
    table.setEditTriggers(QTableWidget.NoEditTriggers)
    table.setSelectionBehavior(QTableWidget.SelectRows)
    table.setAlternatingRowColors(True)
    table.verticalHeader().setVisible(False)
    for row, values in enumerate(rows):
        for col, value in enumerate(values):
            table.setItem(row, col, QTableWidgetItem(str(value)))
    return table


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
        metadata, meta = card()
        meta.addWidget(QLabel(f"Authors: {details['authors'] or '—'}"))
        meta.addWidget(
            QLabel(
                f"Journal: {details['journal'] or '—'} · Year: {details['year'] or '—'}"
            )
        )
        meta.addWidget(
            QLabel(f"DOI: {details['doi'] or '—'} · PMID: {details['pmid'] or '—'}")
        )
        meta.addWidget(QLabel(f"Provenance records: {details['provenance_count']}"))
        layout.addWidget(metadata)
        abstract = QTextEdit()
        abstract.setReadOnly(True)
        abstract.setPlainText(details["abstract"] or "No abstract stored.")
        layout.addWidget(abstract, 1)
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class ScreeningDetailDialog(QDialog):
    def __init__(self, detail, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Screening evidence")
        self.resize(780, 620)
        layout = QVBoxLayout(self)
        title = QLabel(detail.title)
        title.setObjectName("dialogTitle")
        title.setWordWrap(True)
        layout.addWidget(title)
        summary, sl = card("Decision")
        sl.addWidget(QLabel(f"Decision: {detail.decision}"))
        sl.addWidget(QLabel(f"Reason: {detail.reason or '—'}"))
        sl.addWidget(QLabel(f"Criteria version: {detail.criteria_version or '—'}"))
        sl.addWidget(QLabel(f"Run ID: {detail.run_id or '—'}"))
        sl.addWidget(QLabel(f"Audit: {detail.audit_id or '—'}"))
        layout.addWidget(summary)
        rules, rl = card("Rule evidence")
        matched = (
            ", ".join(detail.matched_rules) if detail.matched_rules else "None recorded"
        )
        failed = (
            ", ".join(detail.failed_rules) if detail.failed_rules else "None recorded"
        )
        rl.addWidget(QLabel(f"Matched rules: {matched}"))
        rl.addWidget(QLabel(f"Failed rules: {failed}"))
        layout.addWidget(rules)
        note = QLabel(
            "Read-only evidence from the persisted screening result and audit record. Scientific decisions are not edited here."
        )
        note.setWordWrap(True)
        note.setObjectName("pageSubtitle")
        layout.addWidget(note)
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class NewProjectDialog(QDialog):
    def __init__(
        self, workflow: GuiWorkflowService, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.workflow = workflow
        self.created_project = None
        self.setWindowTitle("New review project")
        self.resize(540, 500)
        layout = QVBoxLayout(self)
        self.name = self._field(layout, "Project name")
        self.question = self._field(layout, "Research question")
        self.topic = self._field(layout, "Topic (required)")
        layout.addWidget(QLabel("Inclusion rules (one per line)"))
        self.inclusion = QTextEdit()
        self.inclusion.setFixedHeight(90)
        layout.addWidget(self.inclusion)
        layout.addWidget(QLabel("Exclusion rules (one per line)"))
        self.exclusion = QTextEdit()
        self.exclusion.setFixedHeight(90)
        layout.addWidget(self.exclusion)
        self.error = QLabel("")
        self.error.setObjectName("pageSubtitle")
        self.error.setWordWrap(True)
        layout.addWidget(self.error)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._create)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @staticmethod
    def _field(layout: QVBoxLayout, label: str) -> QLineEdit:
        layout.addWidget(QLabel(label))
        field = QLineEdit()
        layout.addWidget(field)
        return field

    @staticmethod
    def _lines(widget: QTextEdit) -> tuple[str, ...]:
        return tuple(
            line.strip() for line in widget.toPlainText().splitlines() if line.strip()
        )

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
    def __init__(
        self, workflow: GuiWorkflowService, projects, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.workflow = workflow
        self.projects = list(projects)
        self.outcome = None
        self.setWindowTitle("Import & screen")
        self.resize(600, 280)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Review project"))
        self.project_box = QComboBox()
        for project in self.projects:
            self.project_box.addItem(
                f"{project.name} · {project.criteria.topic}", str(project.project_id)
            )
        layout.addWidget(self.project_box)
        layout.addWidget(QLabel("Source file (.csv, .xlsx, .ris)"))
        row = QHBoxLayout()
        self.path_field = QLineEdit()
        self.path_field.setReadOnly(True)
        row.addWidget(self.path_field, 1)
        browse = QPushButton("Browse…")
        browse.clicked.connect(self._browse)
        row.addWidget(browse)
        layout.addLayout(row)
        self.error = QLabel("")
        self.error.setObjectName("pageSubtitle")
        self.error.setWordWrap(True)
        layout.addWidget(self.error)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._run)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Choose bibliographic file",
            str(Path.home()),
            "Bibliography (*.csv *.xlsx *.ris)",
        )
        if path:
            self.path_field.setText(path)

    def _run(self):
        if not self.path_field.text():
            self.error.setText("Choose a source file first.")
            return
        if not self.projects:
            self.error.setText("Create a review project first.")
            return
        try:
            self.outcome = self.workflow.import_and_screen(
                UUID(self.project_box.currentData()), self.path_field.text()
            )
            self.accept()
        except UnsupportedFileFormat as exc:
            self.error.setText(str(exc))
        except Exception as exc:
            self.error.setText(str(exc))


class DashboardPage(QWidget):
    def __init__(
        self,
        data: GuiDataService,
        refresh_all: Callable[[], None],
        new_project: Callable[[], None] | None = None,
    ):
        super().__init__()
        self.data = data
        self.refresh_all = refresh_all
        self.new_project = new_project
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(28, 24, 28, 28)
        self.root.setSpacing(14)
        self.rebuild()

    def rebuild(self):
        while self.root.count():
            item = self.root.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.root.addLayout(
            page_header(
                "Dashboard",
                "A read-only operational view over persisted scientific state.",
            )
        )
        snap = self.data.snapshot()
        if snap.projects == 0 and self.new_project is not None:
            empty, el = card("Get started")
            el.addWidget(
                QLabel(
                    "No projects yet. Create a review protocol to start "
                    "importing, screening and tracking papers."
                )
            )
            start = QPushButton("Create your first project")
            start.setObjectName("primary")
            start.clicked.connect(self.new_project)
            el.addWidget(start, 0, Qt.AlignLeft)
            self.root.addWidget(empty)
            self.root.addStretch()
            return
        metrics = QGridLayout()
        metrics.setSpacing(12)
        metrics.addWidget(metric("Projects", snap.projects, "Review protocols"), 0, 0)
        metrics.addWidget(metric("Papers", snap.papers, "Persisted corpus"), 0, 1)
        metrics.addWidget(
            metric("Screened", snap.screened, "Persisted decisions"), 0, 2
        )
        metrics.addWidget(
            metric("Included", snap.included, "Deterministic result"), 0, 3
        )
        self.root.addLayout(metrics)
        lower = QGridLayout()
        lower.setSpacing(12)
        progress, pl = card("Screening progress")
        ring_row = QHBoxLayout()
        ring = ProgressRing()
        ring.set_value(snap.screened, snap.papers)
        ring_row.addWidget(ring)
        ring_text = QVBoxLayout()
        ring_text.addWidget(
            QLabel(
                f"{snap.screened:,} of {snap.papers:,} papers have persisted screening results."
            )
        )
        ring_text.addStretch()
        ring_row.addLayout(ring_text, 1)
        pl.addLayout(ring_row)
        lower.addWidget(progress, 0, 0)
        sources, sl = card("Acquisition footprint")
        if snap.source_counts:
            for source, count in snap.source_counts:
                sl.addWidget(
                    QLabel(f"{source.upper()} · {count:,} acquisition batch(es)")
                )
        else:
            sl.addWidget(QLabel("No acquisition batches recorded."))
        lower.addWidget(sources, 0, 1)
        boundary, bl = card("Methodological boundary")
        bl.addWidget(QLabel("Authority: deterministic ScreeningEngine"))
        bl.addWidget(
            QLabel("Provenance: retained across acquisition and synchronization")
        )
        bl.addWidget(
            QLabel(
                "AI/NLP: auxiliary only; never silently changes scientific decisions"
            )
        )
        lower.addWidget(boundary, 1, 0, 1, 2)
        self.root.addLayout(lower)
        self.root.addStretch()


class ProjectsPage(QWidget):
    def __init__(
        self,
        data: GuiDataService,
        workflow: GuiWorkflowService,
        refresh_all: Callable[[], None],
        open_project: Callable[[str], None],
    ) -> None:
        super().__init__()
        self.data = data
        self.workflow = workflow
        self.refresh_all = refresh_all
        self.open_project = open_project
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 28)
        root.setSpacing(14)
        top = QHBoxLayout()
        top.addLayout(
            page_header(
                "Projects", "Review protocols persisted in the project repository."
            )
        )
        top.addStretch()
        button = QPushButton("New project")
        button.setToolTip("Create a review protocol.")
        button.clicked.connect(self._new)
        top.addWidget(button)
        root.addLayout(top)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(
            ["Project", "Topic", "Research question", "Created"]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.doubleClicked.connect(self._open)
        root.addWidget(self.table, 1)
        note = QLabel(
            "Double-click a project to open its workspace and persisted screening runs. Protocol semantics stay in the application/domain layer."
        )
        note.setObjectName("pageSubtitle")
        note.setWordWrap(True)
        root.addWidget(note)
        self.populate()

    def populate(self):
        projects = self.data.projects()
        self.table.setRowCount(len(projects))
        for r, p in enumerate(projects):
            for c, v in enumerate(
                (
                    p.name,
                    p.criteria.topic,
                    p.research_question,
                    format_timestamp(p.created_at),
                )
            ):
                self.table.setItem(r, c, QTableWidgetItem(str(v)))
            self.table.item(r, 0).setData(Qt.UserRole, str(p.project_id))

    def _open(self):
        row = self.table.currentRow()
        if row >= 0:
            self.open_project(str(self.table.item(row, 0).data(Qt.UserRole)))

    def _new(self):
        dialog = NewProjectDialog(self.workflow, self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_all()


class PapersPage(QWidget):
    def __init__(
        self,
        data: GuiDataService,
        workflow: GuiWorkflowService,
        refresh_all: Callable[[], None],
    ) -> None:
        super().__init__()
        self.data = data
        self.workflow = workflow
        self.refresh_all = refresh_all
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 28)
        root.setSpacing(12)
        top = QHBoxLayout()
        top.addLayout(page_header("Papers", "Stored corpus, metadata and provenance."))
        top.addStretch()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search title, DOI, PMID, journal…")
        self.search.setMaximumWidth(340)
        top.addWidget(self.search)
        button = QPushButton("Import && screen…")
        button.setToolTip(
            "Import CSV, Excel or RIS and use the existing screening pipeline."
        )
        button.clicked.connect(self._import)
        top.addWidget(button)
        root.addLayout(top)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Title", "Year", "Journal", "DOI", "PMID"]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.doubleClicked.connect(self._open)
        self.search.textChanged.connect(self._filter)
        root.addWidget(self.table, 1)
        hint = QLabel("Double-click a paper to inspect stored metadata and provenance.")
        hint.setObjectName("pageSubtitle")
        root.addWidget(hint)
        self.rows = data.papers()
        self.populate()

    def populate(self):
        self.table.setRowCount(len(self.rows))
        for r, p in enumerate(self.rows):
            for c, v in enumerate(
                (
                    p.title,
                    p.publication_year or "—",
                    p.journal or "—",
                    p.doi or "—",
                    p.pmid or "—",
                )
            ):
                self.table.setItem(r, c, QTableWidgetItem(str(v)))
            self.table.item(r, 0).setData(Qt.UserRole, str(p.id))

    def _filter(self, text):
        q = text.casefold().strip()
        for r in range(self.table.rowCount()):
            self.table.setRowHidden(
                r,
                q
                not in " ".join(
                    self.table.item(r, c).text()
                    for c in range(self.table.columnCount())
                ).casefold(),
            )

    def _open(self):
        r = self.table.currentRow()
        if r >= 0:
            details = self.data.paper_details(self.table.item(r, 0).data(Qt.UserRole))
            if details:
                PaperDialog(details, self).exec()

    def _import(self):
        dialog = ImportScreenDialog(self.workflow, self.data.projects(), self)
        if dialog.exec() == QDialog.Accepted and dialog.outcome:
            o = dialog.outcome
            QMessageBox.information(
                self,
                "Import & screen complete",
                f"Input: {o.total_input}\nUnique: {o.unique_papers}\nDuplicates removed: {o.duplicates_removed}\nScreened: {o.screened_papers}\nIncluded: {o.included} · Excluded: {o.excluded}\n\nRun ID: {o.run_id}",
            )
            self.refresh_all()


class SourcesPage(QWidget):
    def __init__(self, data: GuiDataService):
        super().__init__()
        self.data = data
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 28)
        root.setSpacing(12)
        top = QHBoxLayout()
        top.addLayout(
            page_header(
                "Sources", "Connection visibility for bibliographic acquisition."
            )
        )
        top.addStretch()
        refresh = QPushButton("Refresh sources")
        refresh.setObjectName("secondary")
        refresh.clicked.connect(self.rebuild)
        top.addWidget(refresh)
        root.addLayout(top)
        self.list = QListWidget()
        self.list.setSpacing(6)
        root.addWidget(self.list, 1)
        self.rebuild()

    def rebuild(self):
        self.list.clear()
        for source in self.data.sources():
            item = QListWidgetItem(
                f"{source.display_name} · {source.status.upper()}"
                + (f" · {source.detail}" if source.detail else "")
            )
            item.setToolTip(
                f"Source key: {source.key}\nStatus: {source.status}\n{source.detail}"
            )
            self.list.addItem(item)


class ScreeningPage(QWidget):
    def __init__(self, data: GuiDataService):
        super().__init__()
        self.data = data
        self.context_run_id = None
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 28)
        root.setSpacing(12)
        top = QHBoxLayout()
        top.addLayout(
            page_header(
                "Screening", "Persisted scientific decisions and their evidence."
            )
        )
        top.addStretch()
        self.context_label = QLabel("All persisted results")
        self.context_label.setObjectName("pageSubtitle")
        top.addWidget(self.context_label)
        self.filter = QComboBox()
        self.filter.addItems(["All decisions", "Included", "Excluded"])
        self.filter.currentTextChanged.connect(self.apply_filter)
        top.addWidget(self.filter)
        root.addLayout(top)
        controls = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search paper, reason, criteria version…")
        self.search.textChanged.connect(self.apply_search)
        controls.addWidget(self.search, 1)
        clear = QPushButton("All runs")
        clear.setObjectName("secondary")
        clear.clicked.connect(self.clear_context)
        controls.addWidget(clear)
        refresh = QPushButton("Refresh")
        refresh.setObjectName("secondary")
        refresh.clicked.connect(self.refresh)
        controls.addWidget(refresh)
        root.addLayout(controls)
        root.addWidget(
            QLabel(
                "Read-only evidence: the GUI does not create or alter scientific decisions. Double-click a row to inspect its persisted evidence."
            )
        )
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Paper", "Year", "Decision", "Reason", "Criteria version"]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.doubleClicked.connect(self._open_detail)
        root.addWidget(self.table, 1)
        self.rows = data.screening_rows()
        self.populate()

    def populate(self):
        visible_rows = tuple(
            x
            for x in self.rows
            if self.context_run_id is None or x.run_id == self.context_run_id
        )
        self.table.setRowCount(len(visible_rows))
        for r, x in enumerate(visible_rows):
            for c, v in enumerate(
                (
                    x.title,
                    x.year or "—",
                    x.decision,
                    x.reason,
                    x.criteria_version or "—",
                )
            ):
                self.table.setItem(r, c, QTableWidgetItem(str(v)))
            self.table.item(r, 0).setData(Qt.UserRole, (x.paper_id, x.run_id))
        self.apply_search(self.search.text())

    def apply_filter(self, value):
        self.apply_search(self.search.text())

    def apply_search(self, text):
        decision = self.filter.currentText()
        q = text.casefold().strip()
        for r in range(self.table.rowCount()):
            row_text = " ".join(
                self.table.item(r, c).text() for c in range(self.table.columnCount())
            ).casefold()
            decision_ok = (
                decision == "All decisions" or self.table.item(r, 2).text() == decision
            )
            search_ok = not q or q in row_text
            self.table.setRowHidden(r, not (decision_ok and search_ok))

    def set_run_context(self, run_id: str) -> None:
        self.context_run_id = run_id
        self.context_label.setText(f"Run context: {run_id}")
        self.populate()

    def clear_context(self) -> None:
        self.context_run_id = None
        self.context_label.setText("All persisted results")
        self.populate()

    def refresh(self):
        self.rows = self.data.screening_rows()
        self.populate()

    def _open_detail(self):
        r = self.table.currentRow()
        if r < 0:
            return
        paper_id, run_id = self.table.item(r, 0).data(Qt.UserRole)
        detail = self.data.screening_detail(paper_id, run_id)
        if detail:
            ScreeningDetailDialog(detail, self).exec()


class AnalysisPage(QWidget):
    def __init__(self, data: GuiDataService):
        super().__init__()
        self.data = data
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 28)
        root.setSpacing(14)
        root.addLayout(
            page_header(
                "Analysis",
                "Read-only analytical views derived from persisted corpus state.",
            )
        )
        tabs = QTabWidget()
        tabs.addTab(self._overview(), "Overview")
        tabs.addTab(self._rules(), "Rules")
        tabs.addTab(self._exclusions(), "Exclusions")
        tabs.addTab(self._dedup(), "Deduplication")
        tabs.addTab(self._authors(), "Authors")
        tabs.addTab(self._journals(), "Journals")
        tabs.addTab(self._years(), "Years")
        root.addWidget(tabs, 1)

    def _overview(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        q = self.data.metadata_quality()
        frame, fl = card("Metadata quality")
        for label, count in (
            ("Abstract", q.with_abstract),
            ("Authors", q.with_authors),
            ("DOI", q.with_doi),
            ("PMID", q.with_pmid),
            ("Journal", q.with_journal),
            ("Publication year", q.with_year),
        ):
            fl.addWidget(
                QLabel(
                    f"{label}: {count:,}/{q.total_papers:,} · {int(count / q.total_papers * 100) if q.total_papers else 0}%"
                )
            )
        layout.addWidget(frame)
        s = self.data.snapshot()
        frame, fl = card("Decision distribution")
        fl.addWidget(QLabel(f"Included: {s.included:,}"))
        fl.addWidget(QLabel(f"Excluded: {s.excluded:,}"))
        fl.addWidget(QLabel(f"Screened: {s.screened:,}"))
        layout.addWidget(frame)
        layout.addStretch()
        return page

    def _rules(self):
        a = self.data.rule_analysis()
        rows = [
            (x.rule_id, x.matched, x.failed, f"{x.match_rate:.0%}") for x in a.rules
        ]
        return self._table_page(
            "Rule evidence",
            rate_table(["Rule ID", "Matched", "Failed", "Match rate"], rows),
        )

    def _exclusions(self):
        a = self.data.exclusion_reason_analysis()
        rows = [(x.reason, x.count, f"{x.rate:.0%}") for x in a.reasons]
        return self._table_page(
            "Exclusion reasons", rate_table(["Reason", "Count", "Share"], rows)
        )

    def _dedup(self):
        a = self.data.deduplication_analysis()
        frame, fl = card("Deduplication across persisted runs")
        fl.addWidget(QLabel(f"Total input: {a.total_input:,}"))
        fl.addWidget(QLabel(f"Unique papers: {a.unique_papers:,}"))
        fl.addWidget(QLabel(f"Duplicates removed: {a.duplicate_papers:,}"))
        fl.addWidget(QLabel(f"Duplicate rate: {a.duplicate_rate:.0%}"))
        return self._table_page("", frame)

    def _authors(self):
        a = self.data.author_analysis()
        rows = sorted(a.by_author, key=lambda x: -x[1])[:50]
        return self._table_page(
            f"{a.unique_authors:,} authors · {a.author_coverage_rate:.0%} coverage",
            rate_table(["Author", "Papers"], rows),
        )

    def _journals(self):
        a = self.data.journal_analysis()
        rows = sorted(a.by_journal, key=lambda x: -x[1])[:50]
        return self._table_page(
            f"{a.unique_journals:,} journals · {a.journal_coverage_rate:.0%} coverage",
            rate_table(["Journal", "Papers"], rows),
        )

    def _years(self):
        a = self.data.publication_year_analysis()
        span = f"{a.year_min}–{a.year_max}" if a.year_min else "—"
        return self._table_page(
            f"Publication span {span} · {a.year_coverage_rate:.0%} coverage",
            rate_table(["Year", "Papers"], sorted(a.by_year)),
        )

    @staticmethod
    def _table_page(title, widget):
        page = QWidget()
        layout = QVBoxLayout(page)
        if title:
            layout.addWidget(QLabel(title))
        layout.addWidget(widget, 1)
        return page


class ReportsPage(QWidget):
    def __init__(self, data: GuiDataService, workflow: GuiWorkflowService):
        super().__init__()
        self.data = data
        self.workflow = workflow
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 28)
        root.setSpacing(14)
        root.addLayout(
            page_header(
                "Reports",
                "Export persisted screening evidence through the existing reporting layer.",
            )
        )
        top = QHBoxLayout()
        self.run_box = QComboBox()
        self.runs = data.screening_runs()
        for run in self.runs:
            self.run_box.addItem(
                f"{format_timestamp_str(run.started_at)} · {run.criteria_version} · {run.screened_papers:,} screened",
                run.run_id,
            )
        top.addWidget(self.run_box, 1)
        export = QPushButton("Export report…")
        export.setToolTip("Generate JSON and Markdown from the selected run.")
        export.clicked.connect(self._export)
        top.addWidget(export)
        root.addLayout(top)
        frame, fl = card("Persisted runs")
        if self.runs:
            for run in self.runs:
                fl.addWidget(
                    QLabel(
                        f"{format_timestamp_str(run.started_at)} · input {run.total_input:,} · unique {run.unique_papers:,} · screened {run.screened_papers:,}"
                    )
                )
        else:
            fl.addWidget(QLabel("No persisted screening runs recorded yet."))
        root.addWidget(frame)
        root.addWidget(
            QLabel(
                "Reporting reuses existing analyses and renderers; the GUI does not silently rerun screening."
            )
        )
        root.addStretch()

    def _export(self):
        if not self.runs:
            QMessageBox.warning(
                self, "No runs", "There are no persisted screening runs to export yet."
            )
            return
        directory = QFileDialog.getExistingDirectory(
            self, "Choose export folder", str(Path.home())
        )
        if not directory:
            return
        try:
            paths = self.workflow.export_report(
                UUID(self.run_box.currentData()), directory
            )
        except Exception as exc:
            QMessageBox.critical(self, "Export failed", str(exc))
            return
        if paths is None:
            QMessageBox.warning(
                self, "Nothing to export", "No audit evidence was found for this run."
            )
            return
        QMessageBox.information(
            self, "Report exported", f"JSON: {paths[0]}\nMarkdown: {paths[1]}"
        )


class SettingsPage(QWidget):
    def __init__(self, data: GuiDataService):
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 28)
        root.setSpacing(14)
        root.addLayout(
            page_header("Settings", "Runtime paths and methodological safeguards.")
        )
        db, dl = card("Database")
        dl.addWidget(QLabel(str(data.database_path)))
        dl.addWidget(QLabel("Override with PSI_JARVIS_DATABASE_PATH at launch."))
        root.addWidget(db)
        boundary, bl = card("Scientific safeguards")
        bl.addWidget(QLabel("Deterministic screening remains authoritative."))
        bl.addWidget(
            QLabel("Synchronization never resolves metadata conflicts silently.")
        )
        bl.addWidget(QLabel("Credentials and tokens stay outside the source tree."))
        root.addWidget(boundary)
        root.addStretch()


class MainWindow(QMainWindow):
    def __init__(self, data_service: GuiDataService | None = None):
        super().__init__()
        self.setWindowTitle("PSI.JARVIS V.1")
        self.resize(1440, 900)
        self.setMinimumSize(1100, 700)
        self.data = data_service or GuiDataService()
        self.workflow = GuiWorkflowService(self.data.database_path)
        self.pages = QStackedWidget()
        self.pages.setObjectName("mainPageStack")
        self.nav_buttons = []
        self._build_ui()
        self._build_shortcuts()
        self.statusBar().showMessage("Ready · deterministic scientific workspace")

    def _build_shortcuts(self) -> None:
        for i in range(len(NAV_ITEMS)):
            shortcut = QShortcut(QKeySequence(f"Ctrl+{i + 1}"), self)
            shortcut.activated.connect(lambda index=i: self._select_page(index))
        new_project = QShortcut(QKeySequence.New, self)
        new_project.activated.connect(self._new_project_shortcut)
        find = QShortcut(QKeySequence.Find, self)
        find.activated.connect(self._focus_search_shortcut)
        refresh = QShortcut(QKeySequence.Refresh, self)
        refresh.activated.connect(self.refresh_all)
        palette = QShortcut(QKeySequence("Ctrl+K"), self)
        palette.activated.connect(self._open_command_palette)

    def _new_project_shortcut(self) -> None:
        for i, (label, _icon) in enumerate(NAV_ITEMS):
            if label == "Projects":
                self._select_page(i)
                break
        page = self.pages.currentWidget()
        if hasattr(page, "_new"):
            page._new()

    def _focus_search_shortcut(self) -> None:
        page = self.pages.currentWidget()
        search = getattr(page, "search", None)
        if isinstance(search, QLineEdit):
            search.setFocus()
            search.selectAll()

    def _open_command_palette(self) -> None:
        commands = tuple(
            Command(
                title=label,
                subtitle=f"Open {label}",
                icon_label=label,
                run=lambda index=i: self._select_page(index),
            )
            for i, (label, _icon) in enumerate(NAV_ITEMS)
        ) + (
            Command(
                title="New project",
                subtitle="Create a review protocol",
                icon_label="Projects",
                run=self._new_project_shortcut,
            ),
            Command(
                title="Refresh workspace",
                subtitle="Reload all pages from persisted state",
                icon_label="Dashboard",
                run=self.refresh_all,
            ),
        )
        palette = CommandPalette(commands, self)
        palette.show_centered_on(self)

    def _build_ui(self):
        root = QWidget()
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(14, 20, 14, 14)
        side.setSpacing(4)
        brand = QHBoxLayout()
        b = QLabel("PSI.JARVIS")
        b.setObjectName("brand")
        v = QLabel("V.1")
        v.setObjectName("version")
        brand.addWidget(b)
        brand.addWidget(v)
        brand.addStretch()
        side.addLayout(brand)
        tagline = QLabel("Scientific Paper Screening\n& Analysis System")
        tagline.setObjectName("tagline")
        tagline.setWordWrap(True)
        side.addWidget(tagline)
        side.addSpacing(16)
        for i, (label, _glyph) in enumerate(NAV_ITEMS):
            button = QPushButton(label)
            button.setObjectName("nav")
            button.setIcon(nav_icon(label, "#dce7f5" if i == 0 else "#7c93ac"))
            button.setIconSize(QSize(18, 18))
            button.setProperty("active", i == 0)
            button.setToolTip(f"Open {label}")
            button.clicked.connect(
                lambda checked=False, index=i: self._select_page(index)
            )
            self.nav_buttons.append(button)
            side.addWidget(button)
        side.addStretch()
        footer = QLabel(
            "Human methodological authority\n\nDeterministic · Traceable\nReproducible"
        )
        footer.setObjectName("sidebarFooter")
        footer.setWordWrap(True)
        footer.setMinimumWidth(0)
        side.addWidget(footer)
        layout.addWidget(sidebar)
        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.addWidget(self.pages)
        layout.addWidget(content, 1)
        self.setCentralWidget(root)
        self.setStatusBar(QStatusBar())
        self._build_pages()

    def _build_pages(self):
        while self.pages.count():
            widget = self.pages.widget(0)
            self.pages.removeWidget(widget)
            widget.deleteLater()
        for page in (
            DashboardPage(self.data, self.refresh_all, self._new_project_shortcut),
            ProjectsPage(
                self.data, self.workflow, self.refresh_all, self.open_project_workspace
            ),
            PapersPage(self.data, self.workflow, self.refresh_all),
            SourcesPage(self.data),
            ScreeningPage(self.data),
            AnalysisPage(self.data),
            ReportsPage(self.data, self.workflow),
            AuditExplorerView(self.data),
            SettingsPage(self.data),
        ):
            self.pages.addWidget(page)

    def open_project_workspace(self, project_id: str) -> None:
        view = ProjectWorkspaceView(
            self.data, project_id, self.open_screening_run, self
        )
        view.setWindowTitle("Project workspace")
        view.resize(1050, 760)
        view.setWindowModality(Qt.WindowModal)
        view.show()
        self._project_workspace = view

    def open_screening_run(self, run_id: str) -> None:
        self._select_page(4)
        screening = self.pages.widget(4)
        screening.set_run_context(run_id)
        self.statusBar().showMessage(f"Screening · run context {run_id}")

    def _select_page(self, index: int):
        self.pages.setCurrentIndex(index)
        for i, button in enumerate(self.nav_buttons):
            is_active = i == index
            button.setProperty("active", is_active)
            button.setIcon(
                nav_icon(NAV_ITEMS[i][0], "#dce7f5" if is_active else "#7c93ac")
            )
            button.style().unpolish(button)
            button.style().polish(button)
        self.statusBar().showMessage(f"{NAV_ITEMS[index][0]} · ready")

    def refresh_all(self):
        current = self.pages.currentIndex()
        search_texts = self._capture_search_texts()
        self._build_pages()
        self._restore_search_texts(search_texts)
        self._select_page(max(0, current))
        self.statusBar().showMessage("Workspace refreshed")

    def _capture_search_texts(self) -> dict[int, str]:
        texts: dict[int, str] = {}
        for i in range(self.pages.count()):
            search = getattr(self.pages.widget(i), "search", None)
            if isinstance(search, QLineEdit) and search.text():
                texts[i] = search.text()
        return texts

    def _restore_search_texts(self, texts: dict[int, str]) -> None:
        for i, text in texts.items():
            search = getattr(self.pages.widget(i), "search", None)
            if isinstance(search, QLineEdit):
                search.setText(text)


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    apply_theme(app)
    window = MainWindow()
    window.show()
    TutorialDialog(window).exec()
    return app.exec()
