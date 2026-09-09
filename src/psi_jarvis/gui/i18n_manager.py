from __future__ import annotations

import json
import weakref
from collections.abc import Iterable
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QEvent, QLibraryInfo, QObject, QTranslator
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QAbstractButton,
    QComboBox,
    QGroupBox,
    QLabel,
    QLineEdit,
    QListWidget,
    QTableWidget,
    QTabWidget,
    QTextEdit,
    QWidget,
)

LANGUAGES: tuple[tuple[str, str], ...] = (
    ("en", "English"),
    ("es", "Español"),
    ("fr", "Français"),
    ("de", "Deutsch"),
    ("it", "Italiano"),
    ("pt", "Português"),
    ("ja", "日本語"),
    ("zh", "中文"),
    ("ko", "한국어"),
)

BUILTIN: dict[str, dict[str, str]] = {
    "es": {
        "Dashboard": "Panel",
        "Projects": "Proyectos",
        "Papers": "Artículos",
        "Sources": "Fuentes",
        "Screening": "Screening",
        "Analysis": "Análisis",
        "Reports": "Informes",
        "Audit": "Auditoría",
        "Settings": "Configuración",
        "New project": "Nuevo proyecto",
        "Paper details": "Detalles del artículo",
        "Screening evidence": "Evidencia del screening",
        "Decision": "Decisión",
        "Rule evidence": "Evidencia de reglas",
        "Close": "Cerrar",
        "Cancel": "Cancelar",
        "OK": "Aceptar",
        "Refresh": "Actualizar",
        "Overview": "Resumen",
        "Rules": "Reglas",
        "Exclusions": "Exclusiones",
        "Deduplication": "Deduplicación",
        "Authors": "Autores",
        "Journals": "Revistas",
        "Years": "Años",
        "Language": "Idioma",
        "Included": "Incluido",
        "Excluded": "Excluido",
        "All decisions": "Todas las decisiones",
        "All runs": "Todas las ejecuciones",
        "Research question": "Pregunta de investigación",
        "Scientific Paper Screening\n& Analysis System": "Sistema de Screening y Análisis\n& de Artículos Científicos",
        "Human methodological authority\n\nDeterministic · Traceable\nReproducible": "Autoridad metodológica humana\n\nDeterminista · Trazable\nReproducible",
        "Open {0}": "Abrir {0}",
        "No review projects yet": "Aún no hay proyectos de revisión",
        "Create your first review project to define a protocol before importing papers.": "Crea tu primer proyecto de revisión para definir un protocolo antes de importar artículos.",
        "Create your first project": "Crear tu primer proyecto",
        "No review projects": "No hay proyectos de revisión",
        "Create a project to define your research question and screening criteria.": "Crea un proyecto para definir tu pregunta de investigación y los criterios de screening.",
        "No source status available": "No hay estado de fuentes disponible",
        "Bibliographic connection details will appear here when source adapters are available.": "Los detalles de las conexiones bibliográficas aparecerán aquí cuando haya adaptadores de fuentes disponibles.",
        "No screening results": "No hay resultados de screening",
        "Import a bibliographic file and run the deterministic screening pipeline to populate this workspace.": "Importa un archivo bibliográfico y ejecuta el pipeline determinista de screening para completar este espacio de trabajo.",
        "No audit events": "No hay eventos de auditoría",
        "Metadata-change history will appear here after synchronized metadata changes are persisted.": "El historial de cambios de metadatos aparecerá aquí después de que se persistan cambios sincronizados.",
        "AI/NLP assistant": "Asistente de IA/NLP",
        "Ask local AI for auxiliary observations…": "Preguntar a la IA local por observaciones auxiliares…",
        "Use a local Ollama model for auxiliary observations. This never changes the screening decision.": "Usa un modelo local de Ollama para obtener observaciones auxiliares. Esto nunca cambia la decisión de screening.",
        "🤖 JARVIS AI": "🤖 JARVIS IA",
        "Open the local AI assistant. Select a paper in Papers to analyze it.": "Abre el asistente de IA local. Selecciona un artículo en Artículos para analizarlo.",
        "Select a paper to open JARVIS AI.": "Selecciona un artículo para abrir JARVIS IA.",
        "Select a paper and press JARVIS AI again.": "Selecciona un artículo y pulsa JARVIS IA de nuevo.",
        "The selected paper could not be retrieved.": "No se pudo recuperar el artículo seleccionado.",
        "This view has no text search.": "Esta vista no tiene búsqueda de texto.",
        "Workspace refreshed": "Espacio de trabajo actualizado",
        "PRISMA view refreshed": "Vista PRISMA actualizada",
        "No runs": "No hay ejecuciones",
        "There are no persisted screening runs to export yet.": "Todavía no hay ejecuciones de screening persistidas para exportar.",
        "Choose export folder": "Elegir carpeta de exportación",
        "Export failed": "Error de exportación",
        "Nothing to export": "Nada que exportar",
        "No audit evidence was found for this run.": "No se encontró evidencia de auditoría para esta ejecución.",
        "Report exported successfully": "Informe exportado correctamente",
        "JARVIS · Local AI assistant": "JARVIS · Asistente de IA local",
        "Auxiliary scientific assistance through Ollama. JARVIS does not replace ScreeningEngine or modify persisted decisions.": "Asistencia científica auxiliar mediante Ollama. JARVIS no sustituye a ScreeningEngine ni modifica decisiones persistidas.",
        "Paper:": "Artículo:",
        "Untitled": "Sin título",
        "Local model": "Modelo local",
        "Select a local model…": "Selecciona un modelo local…",
        "Refresh models": "Actualizar modelos",
        "Analysis mode": "Modo de análisis",
        "Additional instruction (optional)": "Instrucción adicional (opcional)",
        "e.g. focus on the population and outcomes…": "Ej.: céntrate en la población y los outcomes…",
        "🤖 Analyze with JARVIS": "🤖 Analizar con JARVIS",
        "Run local analysis without altering scientific screening.": "Ejecuta el análisis local sin alterar el screening científico.",
        "Checking local Ollama models…": "Comprobando modelos locales de Ollama…",
        "JARVIS's response will appear here as auxiliary assistance.": "La respuesta de JARVIS aparecerá aquí como asistencia auxiliar.",
        "No local models available": "No hay modelos locales disponibles",
        "AI agent error:": "Error del agente IA:",
        "Error while querying Ollama:": "Error al consultar Ollama:",
        "Select an available local model first.": "Selecciona primero un modelo local disponible.",
        "No stable paper identity is available; the request was not sent.": "No se dispone de una identidad estable del artículo; no se envió la solicitud.",
        "JARVIS is analyzing locally…": "JARVIS está analizando localmente…",
        "Wait for the local request to finish before closing this dialog.": "Espera a que termine la solicitud local antes de cerrar este diálogo.",
        "General observations": "Observaciones generales",
        "Methodology": "Metodología",
        "Population": "Población",
        "Relevant results": "Resultados relevantes",
        "Possible exclusion criteria": "Posibles criterios de exclusión",
        "Scientific summary": "Resumen científico",
        "PSI.JARVIS · Quick tutorial": "PSI.JARVIS · Tutorial rápido",
        "GETTING STARTED": "PRIMEROS PASOS",
        "Welcome to PSI.JARVIS": "Bienvenido a PSI.JARVIS",
        "A reproducible workspace for scientific paper acquisition, deterministic screening, analysis, provenance and reporting. The scientific rules live outside the GUI.": "Un espacio de trabajo reproducible para adquirir artículos científicos, realizar screening determinista, análisis, trazabilidad y generación de informes. Las reglas científicas viven fuera de la GUI.",
        "Workspace": "Espacio de trabajo",
        "1 · Create a project": "1 · Crear un proyecto",
        "Start in Projects and define the research question, topic, inclusion rules and exclusion rules. The protocol is validated by the application/domain layer.": "Empieza en Proyectos y define la pregunta de investigación, el tema, las reglas de inclusión y exclusión. El protocolo es validado por la capa de aplicación/dominio.",
        "2 · Import your corpus": "2 · Importar tu corpus",
        "Use Papers → Import & screen to load CSV, Excel or RIS files. PSI.JARVIS normalizes metadata, removes duplicates and sends the corpus through the same screening pipeline used by the rest of the system.": "Usa Artículos → Importar y hacer screening para cargar archivos CSV, Excel o RIS. PSI.JARVIS normaliza los metadatos, elimina duplicados y envía el corpus por el mismo pipeline de screening utilizado por el resto del sistema.",
        "3 · Review evidence": "3 · Revisar la evidencia",
        "Screening shows persisted decisions and criteria versions. Analysis exposes metadata quality, rules, exclusions, deduplication, authors, journals and publication years.": "Screening muestra las decisiones persistidas y las versiones de los criterios. Análisis expone la calidad de los metadatos, reglas, exclusiones, deduplicación, autores, revistas y años de publicación.",
        "4 · Trace everything": "4 · Trazar todo",
        "Sources shows acquisition status, Audit shows metadata-change history, and provenance is retained across acquisition and synchronization. Conflicts are not silently resolved.": "Fuentes muestra el estado de adquisición, Auditoría muestra el historial de cambios de metadatos y la procedencia se conserva durante la adquisición y sincronización. Los conflictos no se resuelven silenciosamente.",
        "5 · Export the result": "5 · Exportar el resultado",
        "Reports uses the existing reporting layer to generate JSON and Markdown from persisted screening evidence. The GUI does not rerun or reinterpret scientific decisions.": "Informes utiliza la capa de generación existente para crear JSON y Markdown a partir de la evidencia de screening persistida. La GUI no vuelve a ejecutar ni reinterpreta las decisiones científicas.",
        "Open: Workspace": "Abrir: Espacio de trabajo",
        "Open: Projects": "Abrir: Proyectos",
        "Open: Papers": "Abrir: Artículos",
        "Open: Screening / Analysis": "Abrir: Screening / Análisis",
        "Open: Sources / Audit": "Abrir: Fuentes / Auditoría",
        "Open: Reports": "Abrir: Informes",
        "Skip": "Omitir",
        "Back": "Atrás",
        "Next": "Siguiente",
        "Finish": "Finalizar",
        "Runtime paths and methodological safeguards.": "Rutas de ejecución y salvaguardas metodológicas.",
        "Database": "Base de datos",
        "Override with PSI_JARVIS_DATABASE_PATH at launch.": "Puedes cambiarla mediante PSI_JARVIS_DATABASE_PATH al iniciar.",
        "Scientific safeguards": "Salvaguardas científicas",
        "Deterministic screening remains authoritative.": "El screening determinista mantiene la autoridad científica.",
        "Synchronization never resolves metadata conflicts silently.": "La sincronización nunca resuelve conflictos de metadatos silenciosamente.",
        "Credentials and tokens stay outside the source tree.": "Las credenciales y tokens permanecen fuera del árbol de código.",
    },
    "fr": {
        "Dashboard": "Tableau de bord",
        "Projects": "Projets",
        "Papers": "Articles",
        "Sources": "Sources",
        "Screening": "Sélection",
        "Analysis": "Analyse",
        "Reports": "Rapports",
        "Audit": "Audit",
        "Settings": "Paramètres",
        "New project": "Nouveau projet",
        "Close": "Fermer",
        "Cancel": "Annuler",
        "Refresh": "Actualiser",
        "Language": "Langue",
    },
    "de": {
        "Dashboard": "Übersicht",
        "Projects": "Projekte",
        "Papers": "Artikel",
        "Sources": "Quellen",
        "Screening": "Screening",
        "Analysis": "Analyse",
        "Reports": "Berichte",
        "Audit": "Audit",
        "Settings": "Einstellungen",
        "New project": "Neues Projekt",
        "Close": "Schließen",
        "Cancel": "Abbrechen",
        "Refresh": "Aktualisieren",
        "Language": "Sprache",
    },
    "it": {
        "Dashboard": "Dashboard",
        "Projects": "Progetti",
        "Papers": "Articoli",
        "Sources": "Fonti",
        "Analysis": "Analisi",
        "Reports": "Rapporti",
        "Audit": "Audit",
        "Settings": "Impostazioni",
        "New project": "Nuovo progetto",
        "Close": "Chiudi",
        "Cancel": "Annulla",
        "Refresh": "Aggiorna",
        "Language": "Lingua",
    },
    "pt": {
        "Dashboard": "Painel",
        "Projects": "Projetos",
        "Papers": "Artigos",
        "Sources": "Fontes",
        "Analysis": "Análise",
        "Reports": "Relatórios",
        "Audit": "Auditoria",
        "Settings": "Configurações",
        "New project": "Novo projeto",
        "Close": "Fechar",
        "Cancel": "Cancelar",
        "Refresh": "Atualizar",
        "Language": "Idioma",
    },
    "ja": {
        "Dashboard": "ダッシュボード",
        "Projects": "プロジェクト",
        "Papers": "論文",
        "Sources": "情報源",
        "Analysis": "分析",
        "Reports": "レポート",
        "Audit": "監査",
        "Settings": "設定",
        "New project": "新規プロジェクト",
        "Close": "閉じる",
        "Cancel": "キャンセル",
        "Refresh": "更新",
        "Language": "言語",
    },
    "zh": {
        "Dashboard": "仪表板",
        "Projects": "项目",
        "Papers": "论文",
        "Sources": "来源",
        "Analysis": "分析",
        "Reports": "报告",
        "Audit": "审计",
        "Settings": "设置",
        "New project": "新建项目",
        "Close": "关闭",
        "Cancel": "取消",
        "Refresh": "刷新",
        "Language": "语言",
    },
    "ko": {
        "Dashboard": "대시보드",
        "Projects": "프로젝트",
        "Papers": "논문",
        "Sources": "출처",
        "Analysis": "분석",
        "Reports": "보고서",
        "Audit": "감사",
        "Settings": "설정",
        "New project": "새 프로젝트",
        "Close": "닫기",
        "Cancel": "취소",
        "Refresh": "새로 고침",
        "Language": "언어",
    },
}


def _catalog_path(language: str) -> Path:
    return Path(__file__).resolve().parent / "translations" / f"ui_{language}.json"


def _load_catalog(language: str) -> dict[str, str]:
    catalog = dict(BUILTIN.get(language, {}))
    path = _catalog_path(language)
    if path.exists():
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                catalog.update({str(k): str(v) for k, v in payload.items()})
        except (OSError, json.JSONDecodeError):
            pass
    return catalog


class CatalogTranslator(QTranslator):
    def __init__(self, catalog: dict[str, str], parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.catalog = catalog

    def translate(
        self, context: str, source_text: str, disambiguation=None, n: int = -1
    ) -> str:
        return self.catalog.get(source_text, "")


class LanguageManager(QObject):
    """Single application-wide localization service for literal Qt UI text."""

    def __init__(self, application: QCoreApplication) -> None:
        super().__init__(application)
        self.application = application
        self.language = "en"
        self._translator: CatalogTranslator | None = None
        self._qt_translator: QTranslator | None = None
        self._source_cache: weakref.WeakKeyDictionary[QWidget, dict[str, object]] = (
            weakref.WeakKeyDictionary()
        )
        application.installEventFilter(self)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() in (
            QEvent.Type.Show,
            QEvent.Type.LanguageChange,
        ) and isinstance(obj, QWidget):
            self.apply(obj)
        return False

    def set_language(self, language: str) -> None:
        if language not in dict(LANGUAGES):
            raise ValueError(f"Unsupported language: {language}")
        if self._translator:
            self.application.removeTranslator(self._translator)
            self._translator = None
        if self._qt_translator:
            self.application.removeTranslator(self._qt_translator)
            self._qt_translator = None
        self.language = language
        if language != "en":
            self._qt_translator = QTranslator(self.application)
            path = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
            if self._qt_translator.load(f"qtbase_{language}", path):
                self.application.installTranslator(self._qt_translator)
            self._translator = CatalogTranslator(
                _load_catalog(language), self.application
            )
            self.application.installTranslator(self._translator)
        for widget in self.application.topLevelWidgets():
            if isinstance(widget, QWidget):
                self.apply(widget)

    def translate(self, text: str) -> str:
        if self.language == "en":
            return text
        return _load_catalog(self.language).get(text, text)

    def apply(self, root: QWidget) -> None:
        widgets: Iterable[QWidget] = (root, *root.findChildren(QWidget))
        for widget in widgets:
            self._translate_widget(widget)
        for action in root.findChildren(QAction):
            source = self._remember_action(action, "text", action.text())
            action.setText(self.translate(source))
            tooltip = self._remember_action(action, "tooltip", action.toolTip())
            if tooltip:
                action.setToolTip(self.translate(tooltip))
        title = self._remember(root, "window_title", root.windowTitle())
        if title:
            root.setWindowTitle(self.translate(title))

    def _state(self, widget: QWidget) -> dict[str, object]:
        return self._source_cache.setdefault(widget, {})

    def _remember(self, widget: QWidget, key: str, value: str) -> str:
        state = self._state(widget)
        source_key = f"source_{key}"
        if source_key not in state:
            state[source_key] = value
        return str(state[source_key])

    def _remember_action(self, action: QAction, key: str, value: str) -> str:
        key_name = f"_psi_i18n_{key}"
        source = action.property(key_name)
        if source is None:
            action.setProperty(key_name, value)
            return value
        return str(source)

    def _translate_widget(self, widget: QWidget) -> None:
        if isinstance(widget, QGroupBox):
            source = self._remember(widget, "title", widget.title())
            widget.setTitle(self.translate(source))
            tooltip = self._remember(widget, "tooltip", widget.toolTip())
            if tooltip:
                widget.setToolTip(self.translate(tooltip))
        elif isinstance(widget, (QLabel, QAbstractButton)):
            source = self._remember(widget, "text", widget.text())
            widget.setText(self.translate(source))
            tooltip = self._remember(widget, "tooltip", widget.toolTip())
            if tooltip:
                widget.setToolTip(self.translate(tooltip))
        elif isinstance(widget, (QLineEdit, QTextEdit)):
            source = self._remember(widget, "placeholder", widget.placeholderText())
            if source:
                widget.setPlaceholderText(self.translate(source))
        elif isinstance(widget, QComboBox):
            state = self._state(widget)
            sources = state.setdefault(
                "items", [widget.itemText(i) for i in range(widget.count())]
            )
            for index, source in enumerate(sources):
                if index < widget.count():
                    widget.setItemText(index, self.translate(str(source)))
        elif isinstance(widget, QListWidget):
            state = self._state(widget)
            sources = state.setdefault(
                "items", [widget.item(i).text() for i in range(widget.count())]
            )
            for index, source in enumerate(sources):
                if index < widget.count():
                    widget.item(index).setText(self.translate(str(source)))
        elif isinstance(widget, QTabWidget):
            state = self._state(widget)
            sources = state.setdefault(
                "tabs", [widget.tabText(i) for i in range(widget.count())]
            )
            for index, source in enumerate(sources):
                if index < widget.count():
                    widget.setTabText(index, self.translate(str(source)))
        elif isinstance(widget, QTableWidget):
            state = self._state(widget)
            sources = state.setdefault(
                "headers",
                [
                    widget.horizontalHeaderItem(i).text()
                    if widget.horizontalHeaderItem(i)
                    else ""
                    for i in range(widget.columnCount())
                ],
            )
            for index, source in enumerate(sources):
                item = widget.horizontalHeaderItem(index)
                if item:
                    item.setText(self.translate(str(source)))


def install_language_selector(window: QWidget, manager: LanguageManager) -> QComboBox:
    selector = QComboBox(window)
    selector.setObjectName("languageSelector")
    selector.setToolTip("Language")
    for code, name in LANGUAGES:
        selector.addItem(name, code)
    selector.setCurrentIndex(
        next(i for i, (code, _) in enumerate(LANGUAGES) if code == manager.language)
    )
    selector.currentIndexChanged.connect(
        lambda index: manager.set_language(str(selector.itemData(index)))
    )
    sidebar = window.findChild(QWidget, "sidebar")
    if sidebar is not None and sidebar.layout() is not None:
        sidebar.layout().insertWidget(max(0, sidebar.layout().count() - 1), selector)
    manager.apply(window)
    return selector
