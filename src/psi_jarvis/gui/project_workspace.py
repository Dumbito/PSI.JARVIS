from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QTabWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from psi_jarvis.gui.data import GuiDataService, ProjectSnapshot


class ProjectPaperDialog(QDialog):
    """Read-only project-scoped paper details and persisted evidence."""

    def __init__(self, data: GuiDataService, project_id: str, paper_id: str, open_screening: Callable[[str], None] | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.data = data
        self.project_id = project_id
        self.paper_id = paper_id
        self.open_screening = open_screening
        self.setWindowTitle("Paper details")
        self.resize(900, 650)
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        details = self.data.paper_details(self.paper_id)
        if not details:
            root.addWidget(QLabel("This paper is no longer available."))
        else:
            title = QLabel(str(details.get("title") or "Untitled paper"))
            title.setObjectName("dialogTitle")
            title.setWordWrap(True)
            root.addWidget(title)
            tabs = QTabWidget()
            tabs.addTab(self._metadata(details), "Metadata")
            tabs.addTab(self._abstract(details), "Abstract")
            tabs.addTab(self._screening(), "Screening")
            tabs.addTab(self._provenance(), "Provenance")
            root.addWidget(tabs, 1)
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _metadata(self, details: dict) -> QWidget:
        page = QWidget()
        grid = QGridLayout(page)
        fields = (
            ("Authors", details.get("authors") or "—"),
            ("Year", details.get("publication_year") or "—"),
            ("Journal", details.get("journal") or "—"),
            ("DOI", details.get("doi") or "—"),
            ("PMID", details.get("pmid") or "—"),
            ("Provenance records", details.get("provenance_count", 0)),
        )
        for row, (label, value) in enumerate(fields):
            grid.addWidget(QLabel(f"{label}:"), row, 0)
            value_label = QLabel(str(value))
            value_label.setWordWrap(True)
            value_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            grid.addWidget(value_label, row, 1)
        grid.setRowStretch(len(fields), 1)
        return page

    def _abstract(self, details: dict) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        abstract = QLabel(str(details.get("abstract") or "No abstract is available."))
        abstract.setWordWrap(True)
        abstract.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(abstract, 1)
        return page

    @staticmethod
    def _table(headers: list[str], rows: list[tuple]) -> QTableWidget:
        table = QTableWidget(len(rows), len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setStretchLastSection(True)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.verticalHeader().setVisible(False)
        table.setSortingEnabled(True)
        for row, values in enumerate(rows):
            for column, value in enumerate(values):
                table.setItem(row, column, QTableWidgetItem(str(value)))
        return table

    def _screening(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        rows = tuple(row for row in self.data.project_screening_rows(self.project_id) if row.paper_id == self.paper_id)
        table = self._table(
            ["Decision", "Reason", "Criteria version", "Run"],
            [(row.decision, row.reason, row.criteria_version or "—", row.run_id or "—") for row in rows],
        )
        for index, row in enumerate(rows):
            table.item(index, 3).setData(Qt.UserRole, row.run_id)
        table.doubleClicked.connect(lambda: self._open_run(table))
        layout.addWidget(QLabel(f"Persisted screening decisions · {len(rows):,} result(s) · Double-click a run to navigate"))
        layout.addWidget(table, 1)
        return page

    def _open_run(self, table: QTableWidget) -> None:
        if self.open_screening is None:
            return
        row = table.currentRow()
        if row < 0:
            return
        run_id = table.item(row, 3).data(Qt.UserRole)
        if run_id:
            self.open_screening(str(run_id))

    def _provenance(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        rows = tuple(row for row in self.data.project_provenance(self.project_id) if row.paper_id == self.paper_id)
        table = self._table(
            ["Source", "Record ID", "Batch", "Ordinal", "Format", "Mapping", "Raw SHA-256"],
            [
                (row.source_key, row.source_record_id or "—", row.batch_id, row.record_ordinal, f"{row.format_name} {row.format_version}", row.mapping_version, row.raw_record_sha256)
                for row in rows
            ],
        )
        layout.addWidget(QLabel(f"Acquisition provenance · {len(rows):,} record(s)"))
        layout.addWidget(table, 1)
        return page


class ProjectWorkspaceView(QWidget):
    """Project-scoped read-only workspace over persisted PSI.JARVIS state."""

    def __init__(self, data: GuiDataService, project_id: str, open_screening: Callable[[str], None] | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.data = data
        self.project_id = project_id
        self.open_screening = open_screening
        self.tabs = QTabWidget()
        self._paper_dialog: ProjectPaperDialog | None = None
        self._paper_search: QLineEdit | None = None
        self._screening_search: QLineEdit | None = None
        self._papers_table: QTableWidget | None = None
        self._screening_table: QTableWidget | None = None
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        snapshot = self.data.project_snapshot(self.project_id)
        if snapshot is None:
            root.addWidget(QLabel("This project is no longer available."))
            return
        header = QHBoxLayout()
        title = QLabel(snapshot.name)
        title.setObjectName("dialogTitle")
        header.addWidget(title)
        header.addStretch()
        refresh = self._button("Refresh")
        refresh.clicked.connect(self.refresh)
        header.addWidget(refresh)
        root.addLayout(header)
        subtitle = QLabel(f"Topic: {snapshot.topic} · Created: {snapshot.created_at}")
        subtitle.setObjectName("pageSubtitle")
        root.addWidget(subtitle)
        self.tabs.addTab(self._overview(snapshot), "Overview")
        self.tabs.addTab(self._papers(), "Papers")
        self.tabs.addTab(self._screening(), "Screening")
        self.tabs.addTab(self._runs(), "Runs")
        self.tabs.addTab(self._provenance(), "Provenance")
        root.addWidget(self.tabs, 1)
        note = QLabel("Read-only project context. Scientific decisions remain owned by the deterministic screening pipeline.")
        note.setWordWrap(True)
        note.setObjectName("pageSubtitle")
        root.addWidget(note)

    @staticmethod
    def _button(text: str):
        from PySide6.QtWidgets import QPushButton
        button = QPushButton(text)
        button.setObjectName("secondary")
        return button

    @staticmethod
    def _table(headers: list[str], rows: list[tuple]) -> QTableWidget:
        table = QTableWidget(len(rows), len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setStretchLastSection(True)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.verticalHeader().setVisible(False)
        table.setSortingEnabled(True)
        for r, values in enumerate(rows):
            for c, value in enumerate(values):
                table.setItem(r, c, QTableWidgetItem(str(value)))
        return table

    def _overview(self, snapshot: ProjectSnapshot) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        grid = QGridLayout()
        metrics = (("Screening runs", snapshot.screening_runs), ("Screened papers", snapshot.screened_papers), ("Corpus papers", len(self.data.project_papers(self.project_id))), ("Provenance records", len(self.data.project_provenance(self.project_id))))
        for col, (label, value) in enumerate(metrics):
            frame = QWidget()
            frame_layout = QVBoxLayout(frame)
            value_label = QLabel(f"{value:,}")
            value_label.setObjectName("metricValue")
            frame_layout.addWidget(value_label)
            frame_layout.addWidget(QLabel(label))
            grid.addWidget(frame, 0, col)
        layout.addLayout(grid)
        layout.addWidget(QLabel(f"Research question: {snapshot.research_question or '—'}"))
        layout.addWidget(QLabel("Inclusion: " + ("; ".join(snapshot.inclusion) if snapshot.inclusion else "—")))
        layout.addWidget(QLabel("Exclusion: " + ("; ".join(snapshot.exclusion) if snapshot.exclusion else "—")))
        layout.addStretch()
        return page

    def _papers(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        papers = self.data.project_papers(self.project_id)
        search = QLineEdit()
        search.setPlaceholderText("Search this project's papers by title, journal, DOI, or PMID…")
        self._paper_search = search
        table = self._table(["#", "Title", "Year", "Journal", "DOI", "PMID"], [(p.position + 1, p.title, p.year or "—", p.journal or "—", p.doi or "—", p.pmid or "—") for p in papers])
        self._papers_table = table
        table.doubleClicked.connect(lambda: self._open_paper_for_row(table, papers))
        search.textChanged.connect(lambda text: self._filter_table(table, text))
        layout.addWidget(search)
        layout.addWidget(QLabel(f"Canonical corpus · {len(papers):,} papers · Double-click a paper to inspect it"))
        layout.addWidget(table, 1)
        return page

    @staticmethod
    def _filter_table(table: QTableWidget, text: str) -> None:
        needle = text.strip().casefold()
        for row in range(table.rowCount()):
            haystack = " ".join(table.item(row, col).text() if table.item(row, col) else "" for col in range(table.columnCount())).casefold()
            table.setRowHidden(row, bool(needle) and needle not in haystack)

    def _open_paper_for_row(self, table: QTableWidget, papers) -> None:
        row = table.currentRow()
        if row < 0:
            return
        title = table.item(row, 1)
        if title is None:
            return
        paper = next((paper for paper in papers if paper.title == title.text()), None)
        if paper is None:
            return
        self._paper_dialog = ProjectPaperDialog(self.data, self.project_id, str(paper.paper_id), self.open_screening, self)
        self._paper_dialog.show()
        self._paper_dialog.raise_()
        self._paper_dialog.activateWindow()

    def _screening(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        rows = self.data.project_screening_rows(self.project_id)
        search = QLineEdit()
        search.setPlaceholderText("Search this project's screening results…")
        self._screening_search = search
        table = self._table(["Paper", "Year", "Decision", "Reason", "Criteria version"], [(x.title, x.year or "—", x.decision, x.reason, x.criteria_version or "—") for x in rows])
        self._screening_table = table
        for r, x in enumerate(rows):
            table.item(r, 0).setData(Qt.UserRole, x.run_id)
        table.doubleClicked.connect(lambda: self._open_run_for_row(table))
        search.textChanged.connect(lambda text: self._filter_table(table, text))
        layout.addWidget(search)
        layout.addWidget(QLabel(f"Persisted screening results · {len(rows):,} result(s) · Double-click to open run"))
        layout.addWidget(table, 1)
        return page

    def _open_run_for_row(self, table: QTableWidget) -> None:
        if self.open_screening is None:
            return
        row = table.currentRow()
        if row >= 0:
            run_id = table.item(row, 0).data(Qt.UserRole)
            if run_id:
                self.open_screening(str(run_id))

    def _runs(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        runs = tuple(run for run in self.data.screening_runs(limit=100000) if run.project_id == self.project_id)
        table = self._table(["Started", "Criteria", "Input", "Unique", "Duplicates", "Screened"], [(r.started_at, r.criteria_version, r.total_input, r.unique_papers, r.duplicates_removed, r.screened_papers) for r in runs])
        table.doubleClicked.connect(lambda: self._open_run_from_table(table, runs))
        layout.addWidget(QLabel(f"Screening run history · {len(runs):,} run(s) · Double-click to open run"))
        layout.addWidget(table, 1)
        return page

    def _open_run_from_table(self, table: QTableWidget, runs) -> None:
        if self.open_screening is None:
            return
        row = table.currentRow()
        if row >= 0:
            self.open_screening(str(runs[row].run_id))

    def _provenance(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        rows = self.data.project_provenance(self.project_id)
        table = self._table(["Paper", "Source", "Record ID", "Batch", "Ordinal", "Format", "Mapping", "Raw SHA-256"], [(x.title, x.source_key, x.source_record_id or "—", x.batch_id, x.record_ordinal, f"{x.format_name} {x.format_version}", x.mapping_version, x.raw_record_sha256) for x in rows])
        layout.addWidget(QLabel(f"Acquisition provenance · {len(rows):,} record(s)"))
        layout.addWidget(table, 1)
        return page

    def refresh(self) -> None:
        while self.tabs.count():
            widget = self.tabs.widget(0)
            self.tabs.removeTab(0)
            widget.deleteLater()
        self._paper_search = None
        self._screening_search = None
        self._papers_table = None
        self._screening_table = None
        snapshot = self.data.project_snapshot(self.project_id)
        if snapshot is None:
            return
        self.tabs.addTab(self._overview(snapshot), "Overview")
        self.tabs.addTab(self._papers(), "Papers")
        self.tabs.addTab(self._screening(), "Screening")
        self.tabs.addTab(self._runs(), "Runs")
        self.tabs.addTab(self._provenance(), "Provenance")
