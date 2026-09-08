from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from psi_jarvis.gui.data import GuiDataService, AuditRow


class AuditExplorerDialog(QDialog):
    """Read-only inspection of a metadata-history event and its provenance."""

    def __init__(self, data: GuiDataService, audit: AuditRow, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.data = data
        self.audit = audit
        self.setWindowTitle("Audit event")
        self.resize(900, 620)
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        title = QLabel("Metadata change audit")
        title.setObjectName("dialogTitle")
        root.addWidget(title)
        grid = QGridLayout()
        fields = (
            ("Changed at", self.audit.changed_at),
            ("Paper ID", self.audit.paper_id),
            ("Source", self.audit.source_key),
            ("Source record", self.audit.source_record_id or "—"),
            ("Changed fields", ", ".join(self.audit.changed_fields) or "—"),
        )
        for row, (label, value) in enumerate(fields):
            grid.addWidget(QLabel(f"{label}:"), row, 0)
            value_label = QLabel(str(value))
            value_label.setWordWrap(True)
            value_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            grid.addWidget(value_label, row, 1)
        root.addLayout(grid)

        details = self.data.paper_details(self.audit.paper_id)
        if details:
            paper_label = QLabel(str(details.get("title") or "Untitled paper"))
            paper_label.setWordWrap(True)
            root.addWidget(paper_label)

        provenance = self.data.paper_provenance(self.audit.paper_id)
        root.addWidget(QLabel(f"Provenance linked to this paper · {len(provenance):,} record(s)"))
        table = QTableWidget(len(provenance), 6)
        table.setHorizontalHeaderLabels(["Source", "Record ID", "Batch", "Ordinal", "Format", "Raw SHA-256"])
        table.horizontalHeader().setStretchLastSection(True)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.verticalHeader().setVisible(False)
        for row, item in enumerate(provenance):
            values = (
                item.source_key,
                item.source_record_id or "—",
                item.batch_id,
                item.record_ordinal,
                f"{item.format_name} {item.format_version}",
                item.raw_record_sha256,
            )
            for column, value in enumerate(values):
                table.setItem(row, column, QTableWidgetItem(str(value)))
        root.addWidget(table, 1)

        note = QLabel("Read-only audit evidence. This view does not modify metadata, provenance, or scientific decisions.")
        note.setWordWrap(True)
        note.setObjectName("pageSubtitle")
        root.addWidget(note)
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)


class AuditExplorerView(QWidget):
    """Project-independent, read-only audit browser."""

    def __init__(self, data: GuiDataService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.data = data
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search paper ID, source, record ID, or changed field…")
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Changed at", "Paper ID", "Source", "Source record", "Changed fields"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.doubleClicked.connect(self._open)
        self.search.textChanged.connect(self._filter)
        root = QVBoxLayout(self)
        root.addWidget(self.search)
        root.addWidget(QLabel("Metadata history · double-click an event to inspect its provenance"))
        root.addWidget(self.table, 1)
        self.populate()

    def populate(self) -> None:
        self.rows = self.data.audit_rows(limit=10000)
        self.table.setRowCount(len(self.rows))
        for row, audit in enumerate(self.rows):
            values = (audit.changed_at, audit.paper_id, audit.source_key, audit.source_record_id or "—", ", ".join(audit.changed_fields))
            for column, value in enumerate(values):
                self.table.setItem(row, column, QTableWidgetItem(str(value)))
        self._filter(self.search.text())

    def _filter(self, text: str) -> None:
        needle = text.strip().casefold()
        for row in range(self.table.rowCount()):
            value = " ".join(self.table.item(row, column).text() if self.table.item(row, column) else "" for column in range(self.table.columnCount())).casefold()
            self.table.setRowHidden(row, bool(needle) and needle not in value)

    def _open(self) -> None:
        row = self.table.currentRow()
        if row < 0 or row >= len(self.rows):
            return
        AuditExplorerDialog(self.data, self.rows[row], self).exec()
