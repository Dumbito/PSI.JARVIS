from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QTabWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from psi_jarvis.gui.data import GuiDataService, ProjectSnapshot


class ProjectPaperDialog(QDialog):
    """Read-only project-scoped paper details and persisted evidence."""
    def __init__(self, data: GuiDataService, project_id: str, paper_id: str, open_screening: Callable[[str], None] | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent); self.data=data; self.project_id=project_id; self.paper_id=paper_id; self.open_screening=open_screening; self.setWindowTitle("Paper details"); self.resize(900,680); self._build()
    def _build(self)->None:
        root=QVBoxLayout(self); details=self.data.paper_details(self.paper_id)
        if not details: root.addWidget(QLabel("This paper is no longer available."))
        else:
            title=QLabel(str(details.get("title") or "Untitled paper")); title.setObjectName("dialogTitle"); title.setWordWrap(True); root.addWidget(title)
            tabs=QTabWidget(); tabs.addTab(self._metadata(details),"Metadata"); tabs.addTab(self._abstract(details),"Abstract"); tabs.addTab(self._screening(),"Screening"); tabs.addTab(self._provenance(),"Provenance"); tabs.addTab(self._evidence(),"Evidence"); root.addWidget(tabs,1)
        buttons=QDialogButtonBox(QDialogButtonBox.Close); buttons.rejected.connect(self.reject); root.addWidget(buttons)
    def _metadata(self,details:dict)->QWidget:
        page=QWidget(); grid=QGridLayout(page); fields=(("Authors",details.get("authors") or "—"),("Year",details.get("year") or "—"),("Journal",details.get("journal") or "—"),("DOI",details.get("doi") or "—"),("PMID",details.get("pmid") or "—"),("Provenance records",details.get("provenance_count",0)))
        for row,(label,value) in enumerate(fields):
            grid.addWidget(QLabel(f"{label}:"),row,0); value_label=QLabel(str(value)); value_label.setWordWrap(True); value_label.setTextInteractionFlags(Qt.TextSelectableByMouse); grid.addWidget(value_label,row,1)
        grid.setRowStretch(len(fields),1); return page
    def _abstract(self,details:dict)->QWidget:
        page=QWidget(); layout=QVBoxLayout(page); abstract=QLabel(str(details.get("abstract") or "No abstract is available.")); abstract.setWordWrap(True); abstract.setTextInteractionFlags(Qt.TextSelectableByMouse); layout.addWidget(abstract,1); return page
    @staticmethod
    def _table(headers:list[str],rows:list[tuple])->QTableWidget:
        table=QTableWidget(len(rows),len(headers)); table.setHorizontalHeaderLabels(headers); table.horizontalHeader().setStretchLastSection(True); table.setSelectionBehavior(QTableWidget.SelectRows); table.setEditTriggers(QTableWidget.NoEditTriggers); table.setAlternatingRowColors(True); table.verticalHeader().setVisible(False)
        for row,values in enumerate(rows):
            for column,value in enumerate(values): table.setItem(row,column,QTableWidgetItem(str(value)))
        return table
    def _screening(self)->QWidget:
        page=QWidget(); layout=QVBoxLayout(page); rows=tuple(row for row in self.data.project_screening_rows(self.project_id) if row.paper_id==self.paper_id); table=self._table(["Decision","Reason","Criteria version","Run"],[(row.decision,row.reason,row.criteria_version or "—",row.run_id or "—") for row in rows])
        for index,row in enumerate(rows): table.item(index,3).setData(Qt.UserRole,row.run_id)
        table.doubleClicked.connect(lambda:self._open_run(table)); layout.addWidget(QLabel(f"Persisted screening decisions · {len(rows):,} result(s) · Double-click a run to navigate")); layout.addWidget(table,1); return page
    def _open_run(self,table:QTableWidget)->None:
        if self.open_screening is None:return
        row=table.currentRow()
        if row<0:return
        run_id=table.item(row,3).data(Qt.UserRole)
        if run_id:self.open_screening(str(run_id))
    def _provenance(self)->QWidget:
        page=QWidget(); layout=QVBoxLayout(page); rows=tuple(row for row in self.data.project_provenance(self.project_id) if row.paper_id==self.paper_id); table=self._table(["Source","Record ID","Batch","Ordinal","Format","Mapping","Raw SHA-256"],[(row.source_key,row.source_record_id or "—",row.batch_id,row.record_ordinal,f"{row.format_name} {row.format_version}",row.mapping_version,row.raw_record_sha256) for row in rows]); layout.addWidget(QLabel(f"Acquisition provenance · {len(rows):,} record(s)")); layout.addWidget(table,1); return page
    def _evidence(self)->QWidget:
        page=QWidget(); layout=QVBoxLayout(page); rows=tuple(row for row in self.data.project_screening_rows(self.project_id) if row.paper_id==self.paper_id)
        if not rows: layout.addWidget(QLabel("No persisted screening evidence is available for this paper in this project.")); layout.addStretch(); return page
        for row in rows:
            detail=self.data.screening_detail(self.paper_id,row.run_id)
            if detail is None: continue
            block=QWidget(); block_layout=QVBoxLayout(block); block_layout.addWidget(QLabel(f"Run: {detail.run_id or '—'} · Criteria: {detail.criteria_version or '—'}")); block_layout.addWidget(QLabel(f"Decision: {detail.decision}")); block_layout.addWidget(QLabel(f"Reason: {detail.reason or '—'}")); block_layout.addWidget(QLabel("Matched rules: "+(", ".join(detail.matched_rules) if detail.matched_rules else "—"))); block_layout.addWidget(QLabel("Failed rules: "+(", ".join(detail.failed_rules) if detail.failed_rules else "—"))); block_layout.addWidget(QLabel(f"Audit ID: {detail.audit_id or '—'}")); layout.addWidget(block)
        layout.addStretch(); return page


class ScreeningRunDialog(QDialog):
    """Read-only inspection of one persisted screening run."""
    def __init__(self,data:GuiDataService,project_id:str,run_id:str,open_paper:Callable[[str],None]|None=None,open_screening:Callable[[str],None]|None=None,parent:QWidget|None=None)->None:
        super().__init__(parent); self.data=data; self.project_id=project_id; self.run_id=run_id; self.open_paper=open_paper; self.open_screening=open_screening; self.setWindowTitle("Screening run"); self.resize(1000,700); self._build()
    def _build(self)->None:
        root=QVBoxLayout(self); run=next((x for x in self.data.screening_runs(limit=100000) if x.run_id==self.run_id),None)
        if run is None: root.addWidget(QLabel("This screening run is no longer available.")); self._close(root); return
        title=QLabel(f"Screening run · {run.run_id}"); title.setObjectName("dialogTitle"); title.setWordWrap(True); root.addWidget(title)
        summary=QGridLayout(); values=(("Started",run.started_at),("Criteria",run.criteria_version or "—"),("Input",run.total_input),("Unique",run.unique_papers),("Duplicates removed",run.duplicates_removed),("Screened",run.screened_papers))
        for row,(label,value) in enumerate(values): summary.addWidget(QLabel(f"{label}:"),row//2*1,row%2*2); summary.addWidget(QLabel(str(value)),row//2,row%2*2+1)
        root.addLayout(summary)
        rows=tuple(x for x in self.data.project_screening_rows(self.project_id) if x.run_id==self.run_id); table=QTableWidget(len(rows),5); table.setHorizontalHeaderLabels(["Paper","Year","Decision","Reason","Criteria version"]); table.horizontalHeader().setStretchLastSection(True); table.setSelectionBehavior(QTableWidget.SelectRows); table.setEditTriggers(QTableWidget.NoEditTriggers); table.setAlternatingRowColors(True); table.verticalHeader().setVisible(False)
        for r,item in enumerate(rows):
            for c,value in enumerate((item.title,item.year or "—",item.decision,item.reason,item.criteria_version or "—")): table.setItem(r,c,QTableWidgetItem(str(value)))
            table.item(r,0).setData(Qt.UserRole,item.paper_id)
        table.doubleClicked.connect(lambda:self._open_selected(table)); root.addWidget(QLabel(f"Persisted results in this run · {len(rows):,} result(s) · Double-click a paper to inspect it")); root.addWidget(table,1)
        actions=QHBoxLayout()
        if self.open_screening is not None:
            from PySide6.QtWidgets import QPushButton
            button=QPushButton("Open in Screening"); button.clicked.connect(lambda:self.open_screening(self.run_id)); actions.addWidget(button)
        actions.addStretch(); close=QDialogButtonBox(QDialogButtonBox.Close); close.rejected.connect(self.reject); actions.addWidget(close); root.addLayout(actions)
    def _close(self,root:QVBoxLayout)->None:
        buttons=QDialogButtonBox(QDialogButtonBox.Close); buttons.rejected.connect(self.reject); root.addWidget(buttons)
    def _open_selected(self,table:QTableWidget)->None:
        if self.open_paper is None:return
        row=table.currentRow()
        if row>=0:
            paper_id=table.item(row,0).data(Qt.UserRole)
            if paper_id:self.open_paper(str(paper_id))


class ProjectWorkspaceView(QWidget):
    """Project-scoped read-only workspace over persisted PSI.JARVIS state."""
    def __init__(self,data:GuiDataService,project_id:str,open_screening:Callable[[str],None]|None=None,parent:QWidget|None=None)->None:
        super().__init__(parent); self.data=data; self.project_id=project_id; self.open_screening=open_screening; self.tabs=QTabWidget(); self._paper_dialog=None; self._run_dialog=None; self._build()
    def _build(self)->None:
        root=QVBoxLayout(self); snapshot=self.data.project_snapshot(self.project_id)
        if snapshot is None: root.addWidget(QLabel("This project is no longer available.")); return
        header=QHBoxLayout(); title=QLabel(snapshot.name); title.setObjectName("dialogTitle"); header.addWidget(title); header.addStretch(); from PySide6.QtWidgets import QPushButton; refresh=QPushButton("Refresh"); refresh.setObjectName("secondary"); refresh.clicked.connect(self.refresh); header.addWidget(refresh); root.addLayout(header)
        subtitle=QLabel(f"Topic: {snapshot.topic} · Created: {snapshot.created_at}"); subtitle.setObjectName("pageSubtitle"); root.addWidget(subtitle)
        self.tabs.addTab(self._overview(snapshot),"Overview"); self.tabs.addTab(self._papers(),"Papers"); self.tabs.addTab(self._screening(),"Screening"); self.tabs.addTab(self._runs(),"Runs"); self.tabs.addTab(self._provenance(),"Provenance"); root.addWidget(self.tabs,1)
        note=QLabel("Read-only project context. Scientific decisions remain owned by the deterministic screening pipeline."); note.setWordWrap(True); note.setObjectName("pageSubtitle"); root.addWidget(note)
    @staticmethod
    def _table(headers:list[str],rows:list[tuple])->QTableWidget:
        table=QTableWidget(len(rows),len(headers)); table.setHorizontalHeaderLabels(headers); table.horizontalHeader().setStretchLastSection(True); table.setSelectionBehavior(QTableWidget.SelectRows); table.setEditTriggers(QTableWidget.NoEditTriggers); table.setAlternatingRowColors(True); table.verticalHeader().setVisible(False)
        for r,values in enumerate(rows):
            for c,value in enumerate(values): table.setItem(r,c,QTableWidgetItem(str(value)))
        return table
    def _overview(self,snapshot:ProjectSnapshot)->QWidget:
        page=QWidget(); layout=QVBoxLayout(page); grid=QGridLayout(); metrics=(("Screening runs",snapshot.screening_runs),("Screened papers",snapshot.screened_papers),("Corpus papers",len(self.data.project_papers(self.project_id))),("Provenance records",len(self.data.project_provenance(self.project_id))))
        for col,(label,value) in enumerate(metrics): frame=QWidget(); fl=QVBoxLayout(frame); value_label=QLabel(f"{value:,}"); value_label.setObjectName("metricValue"); fl.addWidget(value_label); fl.addWidget(QLabel(label)); grid.addWidget(frame,0,col)
        layout.addLayout(grid); layout.addWidget(QLabel(f"Research question: {snapshot.research_question or '—'}")); layout.addWidget(QLabel("Inclusion: "+("; ".join(snapshot.inclusion) if snapshot.inclusion else "—"))); layout.addWidget(QLabel("Exclusion: "+("; ".join(snapshot.exclusion) if snapshot.exclusion else "—"))); layout.addStretch(); return page
    def _papers(self)->QWidget:
        page=QWidget(); layout=QVBoxLayout(page); papers=self.data.project_papers(self.project_id); search=QLineEdit(); search.setPlaceholderText("Search this project's papers by title, journal, DOI, or PMID…"); table=self._table(["#","Title","Year","Journal","DOI","PMID"],[(p.position+1,p.title,p.year or "—",p.journal or "—",p.doi or "—",p.pmid or "—") for p in papers])
        for row,paper in enumerate(papers): table.item(row,1).setData(Qt.UserRole,str(paper.paper_id))
        table.doubleClicked.connect(lambda:self._open_paper_for_row(table)); search.textChanged.connect(lambda text:self._filter_table(table,text)); layout.addWidget(search); layout.addWidget(QLabel(f"Canonical corpus · {len(papers):,} papers · Double-click a paper to inspect it")); layout.addWidget(table,1); return page
    @staticmethod
    def _filter_table(table:QTableWidget,text:str)->None:
        needle=text.strip().casefold()
        for row in range(table.rowCount()): haystack=" ".join(table.item(row,col).text() if table.item(row,col) else "" for col in range(table.columnCount())).casefold(); table.setRowHidden(row,bool(needle) and needle not in haystack)
    def _open_paper_for_row(self,table:QTableWidget)->None:
        row=table.currentRow()
        if row<0:return
        title=table.item(row,1)
        if title is None:return
        paper_id=title.data(Qt.UserRole)
        if not paper_id:return
        self._paper_dialog=ProjectPaperDialog(self.data,self.project_id,str(paper_id),self.open_screening,self); self._paper_dialog.show(); self._paper_dialog.raise_(); self._paper_dialog.activateWindow()
    def _screening(self)->QWidget:
        page=QWidget(); layout=QVBoxLayout(page); rows=self.data.project_screening_rows(self.project_id); search=QLineEdit(); search.setPlaceholderText("Search this project's screening results…"); table=self._table(["Paper","Year","Decision","Reason","Criteria version"],[(x.title,x.year or "—",x.decision,x.reason,x.criteria_version or "—") for x in rows])
        for r,x in enumerate(rows): table.item(r,0).setData(Qt.UserRole,(x.paper_id,x.run_id))
        table.doubleClicked.connect(lambda:self._open_screening_selection(table)); search.textChanged.connect(lambda text:self._filter_table(table,text)); layout.addWidget(search); layout.addWidget(QLabel(f"Persisted screening results · {len(rows):,} result(s) · Double-click a result to inspect its paper")); layout.addWidget(table,1); return page
    def _open_screening_selection(self,table:QTableWidget)->None:
        row=table.currentRow()
        if row<0:return
        value=table.item(row,0).data(Qt.UserRole)
        if not value:return
        paper_id,run_id=value; self._paper_dialog=ProjectPaperDialog(self.data,self.project_id,str(paper_id),self.open_screening,self); self._paper_dialog.show(); self._paper_dialog.raise_(); self._paper_dialog.activateWindow()
        if self.open_screening is not None and run_id:self.open_screening(str(run_id))
    def _runs(self)->QWidget:
        page=QWidget(); layout=QVBoxLayout(page); runs=tuple(run for run in self.data.screening_runs(limit=100000) if run.project_id==self.project_id); table=self._table(["Started","Criteria","Input","Unique","Duplicates","Screened"],[(r.started_at,r.criteria_version,r.total_input,r.unique_papers,r.duplicates_removed,r.screened_papers) for r in runs]); table.doubleClicked.connect(lambda:self._open_run_from_table(table,runs)); layout.addWidget(QLabel(f"Screening run history · {len(runs):,} run(s) · Double-click to inspect run")); layout.addWidget(table,1); return page
    def _open_run_from_table(self,table:QTableWidget,runs)->None:
        row=table.currentRow()
        if row<0:return
        run_id=str(runs[row].run_id); self._run_dialog=ScreeningRunDialog(self.data,self.project_id,run_id,self._open_paper,self.open_screening,self); self._run_dialog.show(); self._run_dialog.raise_(); self._run_dialog.activateWindow()
    def _open_paper(self,paper_id:str)->None:
        self._paper_dialog=ProjectPaperDialog(self.data,self.project_id,paper_id,self.open_screening,self); self._paper_dialog.show(); self._paper_dialog.raise_(); self._paper_dialog.activateWindow()
    def _provenance(self)->QWidget:
        page=QWidget(); layout=QVBoxLayout(page); rows=self.data.project_provenance(self.project_id); table=self._table(["Paper","Source","Record ID","Batch","Ordinal","Format","Mapping","Raw SHA-256"],[(x.title,x.source_key,x.source_record_id or "—",x.batch_id,x.record_ordinal,f"{x.format_name} {x.format_version}",x.mapping_version,x.raw_record_sha256) for x in rows]); layout.addWidget(QLabel(f"Acquisition provenance · {len(rows):,} record(s)")); layout.addWidget(table,1); return page
    def refresh(self)->None:
        while self.tabs.count(): widget=self.tabs.widget(0); self.tabs.removeTab(0); widget.deleteLater()
        snapshot=self.data.project_snapshot(self.project_id)
        if snapshot is None:return
        self.tabs.addTab(self._overview(snapshot),"Overview"); self.tabs.addTab(self._papers(),"Papers"); self.tabs.addTab(self._screening(),"Screening"); self.tabs.addTab(self._runs(),"Runs"); self.tabs.addTab(self._provenance(),"Provenance")
