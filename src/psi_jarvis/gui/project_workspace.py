from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QPushButton, QTabWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from psi_jarvis.gui.data import GuiDataService, ProjectSnapshot


class ProjectWorkspaceView(QWidget):
    """Project-scoped read-only workspace over persisted PSI.JARVIS state."""

    def __init__(self, data: GuiDataService, project_id: str, open_screening: Callable[[str], None] | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.data = data
        self.project_id = project_id
        self.open_screening = open_screening
        self.tabs = QTabWidget()
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        snapshot = self.data.project_snapshot(self.project_id)
        if snapshot is None:
            root.addWidget(QLabel("This project is no longer available."))
            return
        title = QLabel(snapshot.name)
        title.setObjectName("dialogTitle")
        root.addWidget(title)
        subtitle = QLabel(f"Topic: {snapshot.topic} · Created: {snapshot.created_at}")
        subtitle.setObjectName("pageSubtitle")
        root.addWidget(subtitle)
        self.tabs.addTab(self._overview(snapshot), "Overview")
        self.tabs.addTab(self._papers(), "Papers")
        self.tabs.addTab(self._screening(), "Screening")
        self.tabs.addTab(self._runs(), "Runs")
        self.tabs.addTab(self._provenance(), "Provenance")
        root.addWidget(self.tabs, 1)
        root.addWidget(QLabel("Read-only project context. Scientific decisions remain owned by the deterministic screening pipeline."))

    @staticmethod
    def _table(headers: list[str], rows: list[tuple]) -> QTableWidget:
        table = QTableWidget(len(rows), len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setStretchLastSection(True)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.verticalHeader().setVisible(False)
        for r, values in enumerate(rows):
            for c, value in enumerate(values):
                table.setItem(r, c, QTableWidgetItem(str(value)))
        return table

    def _overview(self, snapshot: ProjectSnapshot) -> QWidget:
        page = QWidget(); layout = QVBoxLayout(page)
        grid = QGridLayout()
        for col, (label, value) in enumerate((("Screening runs", snapshot.screening_runs), ("Screened papers", snapshot.screened_papers), ("Corpus papers", len(self.data.project_papers(self.project_id))), ("Provenance records", len(self.data.project_provenance(self.project_id))))):
            frame = QWidget(); fl = QVBoxLayout(frame); value_label = QLabel(f"{value:,}"); value_label.setObjectName("metricValue"); fl.addWidget(value_label); fl.addWidget(QLabel(label)); grid.addWidget(frame, 0, col)
        layout.addLayout(grid)
        layout.addWidget(QLabel(f"Research question: {snapshot.research_question or '—'}"))
        layout.addWidget(QLabel("Inclusion: " + ("; ".join(snapshot.inclusion) if snapshot.inclusion else "—")))
        layout.addWidget(QLabel("Exclusion: " + ("; ".join(snapshot.exclusion) if snapshot.exclusion else "—")))
        layout.addStretch(); return page

    def _papers(self) -> QWidget:
        page = QWidget(); layout = QVBoxLayout(page)
        papers = self.data.project_papers(self.project_id)
        table = self._table(["#", "Title", "Year", "Journal", "DOI", "PMID"], [(p.position + 1, p.title, p.year or "—", p.journal or "—", p.doi or "—", p.pmid or "—") for p in papers])
        layout.addWidget(QLabel(f"Canonical corpus · {len(papers):,} papers")); layout.addWidget(table, 1); return page

    def _screening(self) -> QWidget:
        page = QWidget(); layout = QVBoxLayout(page)
        rows = self.data.project_screening_rows()
        table = self._table(["Paper", "Year", "Decision", "Reason", "Criteria version"], [(x.title, x.year or "—", x.decision, x.reason, x.criteria_version or "—") for x in rows])
        for r, x in enumerate(rows): table.item(r, 0).setData(Qt.UserRole, x.run_id)
        table.doubleClicked.connect(lambda: self._open_run_for_row(table))
        layout.addWidget(QLabel(f"Persisted screening results · {len(rows):,} result(s)")); layout.addWidget(table, 1); return page

    def _open_run_for_row(self, table: QTableWidget) -> None:
        if self.open_screening is None: return
        row = table.currentRow()
        if row >= 0:
            run_id = table.item(row, 0).data(Qt.UserRole)
            if run_id: self.open_screening(str(run_id))

    def _runs(self) -> QWidget:
        page = QWidget(); layout = QVBoxLayout(page)
        runs = tuple(run for run in self.data.screening_runs(limit=100000) if run.project_id == self.project_id)
        table = self._table(["Started", "Criteria", "Input", "Unique", "Duplicates", "Screened"], [(r.started_at, r.criteria_version, r.total_input, r.unique_papers, r.duplicates_removed, r.screened_papers) for r in runs])
        table.doubleClicked.connect(lambda: self._open_run_from_table(table, runs))
        layout.addWidget(table, 1); return page

    def _open_run_from_table(self, table: QTableWidget, runs) -> None:
        if self.open_screening is None: return
        row = table.currentRow()
        if row >= 0: self.open_screening(str(runs[row].run_id))

    def _provenance(self) -> QWidget:
        page = QWidget(); layout = QVBoxLayout(page)
        rows = self.data.project_provenance(self.project_id)
        table = self._table(["Paper", "Source", "Record ID", "Batch", "Ordinal", "Format", "Mapping", "Raw SHA-256"], [(x.title, x.source_key, x.source_record_id or "—", x.batch_id, x.record_ordinal, f"{x.format_name} {x.format_version}", x.mapping_version, x.raw_record_sha256) for x in rows])
        layout.addWidget(QLabel(f"Acquisition provenance · {len(rows):,} record(s)")); layout.addWidget(table, 1); return page
