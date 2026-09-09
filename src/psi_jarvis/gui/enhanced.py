from __future__ import annotations

from pathlib import Path
from uuid import UUID

from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QWidget,
)

from psi_jarvis.gui import app
from psi_jarvis.gui.ai_assistant import AIAssistantDialog
from psi_jarvis.gui.empty_state import EmptyState
from psi_jarvis.gui.i18n import apply_spanish_ui
from psi_jarvis.gui.toast import Toast


class EnhancedPaperDialog(app.PaperDialog):
    def __init__(self, details: dict, parent: QWidget | None = None) -> None:
        self._details = details
        super().__init__(details, parent)
        self.setWindowTitle("Detalles del artículo")
        layout = self.layout()
        if layout is None:
            return
        assistant = QLabel("🤖 JARVIS · Agente IA")
        assistant.setObjectName("sectionTitle")
        layout.insertWidget(max(0, layout.count() - 1), assistant)
        button = QPushButton("🤖 Abrir JARVIS IA")
        button.setToolTip(
            "Analiza el artículo con un modelo local de Ollama. La IA solo proporciona observaciones y nunca cambia la decisión de screening."
        )
        button.clicked.connect(self._open_assistant)
        layout.insertWidget(max(0, layout.count() - 1), button)

    def _open_assistant(self) -> None:
        AIAssistantDialog(self._details, self).exec()


class EnhancedPapersPage(app.PapersPage):
    """Papers page that supplies the stable paper identity to the assistant dialog."""

    def _open(self):
        row = self.table.currentRow()
        if row < 0:
            return
        paper_id = str(self.table.item(row, 0).data(app.Qt.UserRole))
        details = self.data.paper_details(paper_id)
        if details:
            details["paper_id"] = paper_id
            EnhancedPaperDialog(details, self).exec()


class EnhancedDashboardPage(app.DashboardPage):
    def rebuild(self):
        super().rebuild()
        if self.data.snapshot().projects == 0:
            self.root.addWidget(
                EmptyState(
                    "No hay proyectos de revisión",
                    "Crea tu primer proyecto para definir el protocolo antes de importar artículos.",
                    "Crear primer proyecto",
                    self._create_project,
                )
            )

    def _create_project(self) -> None:
        window = self.window()
        if hasattr(window, "pages"):
            window._select_page(1)
            projects = window.pages.widget(1)
            if hasattr(projects, "_new"):
                projects._new()


class EnhancedProjectsPage(app.ProjectsPage):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.empty_state = EmptyState(
            "No hay proyectos de revisión",
            "Crea un proyecto para definir tu pregunta de investigación y los criterios de screening.",
            "Nuevo proyecto",
            self._new,
            self,
        )
        self.layout().addWidget(self.empty_state)
        self._update_empty_state()

    def populate(self):
        super().populate()
        if hasattr(self, "empty_state"):
            self._update_empty_state()

    def _update_empty_state(self):
        self.empty_state.setVisible(self.table.rowCount() == 0)


class EnhancedSourcesPage(app.SourcesPage):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.empty_state = EmptyState(
            "No hay fuentes disponibles",
            "Los detalles de las conexiones bibliográficas aparecerán aquí cuando haya adaptadores disponibles.",
            parent=self,
        )
        self.layout().addWidget(self.empty_state)
        self._update_empty_state()

    def rebuild(self):
        super().rebuild()
        if hasattr(self, "empty_state"):
            self._update_empty_state()

    def _update_empty_state(self):
        self.empty_state.setVisible(self.list.count() == 0)


class EnhancedScreeningPage(app.ScreeningPage):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.empty_state = EmptyState(
            "No hay resultados de screening",
            "Importa un archivo bibliográfico y ejecuta el pipeline determinista para poblar este espacio de trabajo.",
            parent=self,
        )
        self.layout().addWidget(self.empty_state)
        self._update_empty_state()

    def populate(self):
        super().populate()
        if hasattr(self, "empty_state"):
            self._update_empty_state()

    def _update_empty_state(self):
        self.empty_state.setVisible(self.table.rowCount() == 0)


class EnhancedAuditView(app.AuditExplorerView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.empty_state = EmptyState(
            "No hay eventos de auditoría",
            "El historial de cambios de metadatos aparecerá aquí después de sincronizar cambios persistidos.",
            parent=self,
        )
        self.layout().addWidget(self.empty_state)
        self._update_empty_state()

    def populate(self):
        super().populate()
        if hasattr(self, "empty_state"):
            self._update_empty_state()

    def _update_empty_state(self):
        self.empty_state.setVisible(self.table.rowCount() == 0)


class EnhancedReportsPage(app.ReportsPage):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for button in self.findChildren(QPushButton):
            if button.text().replace("&", "").strip().startswith("Refresh PRISMA"):
                button.setText("Actualizar PRISMA")
                button.clicked.connect(lambda: Toast.show_message(self, "Vista PRISMA actualizada"))

    def _export(self):
        if not self.runs:
            QMessageBox.warning(self, "Sin ejecuciones", "Todavía no hay ejecuciones de screening persistidas para exportar.")
            return
        directory = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta de exportación", str(Path.home()))
        if not directory:
            return
        try:
            paths = self.workflow.export_report(UUID(self.run_box.currentData()), directory)
        except Exception as exc:
            QMessageBox.critical(self, "Error de exportación", str(exc))
            return
        if paths is None:
            QMessageBox.warning(self, "Nada para exportar", "No se encontró evidencia de auditoría para esta ejecución.")
            return
        Toast.show_message(self, "Informe exportado correctamente")


class EnhancedMainWindow(app.MainWindow):
    """Scientific window with Spanish presentation and JARVIS AI assistance."""

    def __init__(self, *args, **kwargs):
        self.session_search: dict[str, str] = {"papers": "", "screening": "", "audit": ""}
        super().__init__(*args, **kwargs)
        self._install_shortcuts()
        self._install_ai_button()
        apply_spanish_ui(self)

    def _install_ai_button(self) -> None:
        self._ai_button = QPushButton("🤖 JARVIS IA")
        self._ai_button.setToolTip(
            "Abrir el agente IA local. Selecciona un artículo en la vista Artículos para analizarlo."
        )
        self._ai_button.clicked.connect(self._open_ai_from_workspace)
        self.statusBar().addPermanentWidget(self._ai_button)

    def _open_ai_from_workspace(self) -> None:
        papers = self.pages.widget(2)
        if not hasattr(papers, "table"):
            self._select_page(2)
            Toast.show_message(self, "Selecciona un artículo para abrir JARVIS IA.")
            return
        row = papers.table.currentRow()
        if row < 0:
            self._select_page(2)
            Toast.show_message(self, "Selecciona un artículo y pulsa JARVIS IA de nuevo.")
            return
        paper_id = str(papers.table.item(row, 0).data(app.Qt.UserRole))
        details = papers.data.paper_details(paper_id)
        if not details:
            Toast.show_message(self, "No se pudo recuperar el artículo seleccionado.")
            return
        details["paper_id"] = paper_id
        AIAssistantDialog(details, self).exec()

    def _install_shortcuts(self) -> None:
        self._shortcut_new = QShortcut(QKeySequence("Ctrl+N"), self)
        self._shortcut_new.activated.connect(self._new_project)
        self._shortcut_find = QShortcut(QKeySequence("Ctrl+F"), self)
        self._shortcut_find.activated.connect(self._focus_search)
        self._shortcut_refresh = QShortcut(QKeySequence("Ctrl+R"), self)
        self._shortcut_refresh.activated.connect(self._refresh_with_toast)
        self._shortcut_escape = QShortcut(QKeySequence("Esc"), self)
        self._shortcut_escape.activated.connect(self._close_active_dialog)

    def _new_project(self) -> None:
        projects = self.pages.widget(1)
        if hasattr(projects, "_new"):
            self._select_page(1)
            projects._new()

    def _focus_search(self) -> None:
        page = self.pages.currentWidget()
        search = getattr(page, "search", None)
        if isinstance(search, QLineEdit):
            search.setFocus()
            search.selectAll()
            return
        Toast.show_message(self, "Esta vista no tiene búsqueda de texto.")

    def _refresh_with_toast(self) -> None:
        self.refresh_all()
        Toast.show_message(self, "Espacio de trabajo actualizado")

    def _close_active_dialog(self) -> None:
        for widget in QApplication.topLevelWidgets():
            if widget is not self and widget.isVisible() and widget.isModal():
                widget.close()
                return

    def refresh_all(self):
        self._capture_session_state()
        current = self.pages.currentIndex()
        super().refresh_all()
        self._restore_session_state()
        self._select_page(max(0, current))
        self.statusBar().showMessage("Espacio de trabajo actualizado")
        apply_spanish_ui(self)

    def _capture_session_state(self) -> None:
        mapping = ((2, "papers"), (4, "screening"), (7, "audit"))
        for index, key in mapping:
            page = self.pages.widget(index)
            search = getattr(page, "search", None)
            if isinstance(search, QLineEdit):
                self.session_search[key] = search.text()

    def _restore_session_state(self) -> None:
        mapping = ((2, "papers"), (4, "screening"), (7, "audit"))
        for index, key in mapping:
            page = self.pages.widget(index)
            search = getattr(page, "search", None)
            if isinstance(search, QLineEdit):
                search.setText(self.session_search[key])


def install_presentation_patches() -> None:
    """Patch only GUI classes; deterministic/domain behavior remains untouched."""
    app.PaperDialog = EnhancedPaperDialog
    app.PapersPage = EnhancedPapersPage
    app.DashboardPage = EnhancedDashboardPage
    app.ProjectsPage = EnhancedProjectsPage
    app.SourcesPage = EnhancedSourcesPage
    app.ScreeningPage = EnhancedScreeningPage
    app.AuditExplorerView = EnhancedAuditView
    app.ReportsPage = EnhancedReportsPage
