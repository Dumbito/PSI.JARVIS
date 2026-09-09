from __future__ import annotations

import json
import weakref
from pathlib import Path
from typing import Iterable

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
    ("en", "English"), ("es", "Español"), ("fr", "Français"),
    ("de", "Deutsch"), ("it", "Italiano"), ("pt", "Português"),
    ("ja", "日本語"), ("zh", "中文"), ("ko", "한국어"),
)

BUILTIN: dict[str, dict[str, str]] = {
    "es": {"Dashboard":"Panel", "Projects":"Proyectos", "Papers":"Artículos", "Sources":"Fuentes", "Screening":"Screening", "Analysis":"Análisis", "Reports":"Informes", "Audit":"Auditoría", "Settings":"Configuración", "New project":"Nuevo proyecto", "Paper details":"Detalles del artículo", "Screening evidence":"Evidencia del screening", "Decision":"Decisión", "Rule evidence":"Evidencia de reglas", "Close":"Cerrar", "Cancel":"Cancelar", "OK":"Aceptar", "Refresh":"Actualizar", "Overview":"Resumen", "Rules":"Reglas", "Exclusions":"Exclusiones", "Deduplication":"Deduplicación", "Authors":"Autores", "Journals":"Revistas", "Years":"Años", "Language":"Idioma", "Included":"Incluido", "Excluded":"Excluido", "All decisions":"Todas las decisiones", "All runs":"Todas las ejecuciones"},
    "fr": {"Dashboard":"Tableau de bord", "Projects":"Projets", "Papers":"Articles", "Sources":"Sources", "Screening":"Sélection", "Analysis":"Analyse", "Reports":"Rapports", "Audit":"Audit", "Settings":"Paramètres", "New project":"Nouveau projet", "Paper details":"Détails de l'article", "Screening evidence":"Preuves de sélection", "Decision":"Décision", "Rule evidence":"Preuves des règles", "Close":"Fermer", "Cancel":"Annuler", "OK":"OK", "Refresh":"Actualiser", "Overview":"Vue d'ensemble", "Rules":"Règles", "Exclusions":"Exclusions", "Deduplication":"Déduplication", "Authors":"Auteurs", "Journals":"Revues", "Years":"Années", "Language":"Langue", "Included":"Inclus", "Excluded":"Exclus", "All decisions":"Toutes les décisions", "All runs":"Toutes les exécutions"},
    "de": {"Dashboard":"Übersicht", "Projects":"Projekte", "Papers":"Artikel", "Sources":"Quellen", "Screening":"Screening", "Analysis":"Analyse", "Reports":"Berichte", "Audit":"Audit", "Settings":"Einstellungen", "New project":"Neues Projekt", "Paper details":"Artikeldetails", "Screening evidence":"Screening-Nachweise", "Decision":"Entscheidung", "Rule evidence":"Regelnachweise", "Close":"Schließen", "Cancel":"Abbrechen", "OK":"OK", "Refresh":"Aktualisieren", "Overview":"Übersicht", "Rules":"Regeln", "Exclusions":"Ausschlüsse", "Deduplication":"Duplikatbereinigung", "Authors":"Autoren", "Journals":"Zeitschriften", "Years":"Jahre", "Language":"Sprache", "Included":"Eingeschlossen", "Excluded":"Ausgeschlossen", "All decisions":"Alle Entscheidungen", "All runs":"Alle Ausführungen"},
    "it": {"Dashboard":"Dashboard", "Projects":"Progetti", "Papers":"Articoli", "Sources":"Fonti", "Analysis":"Analisi", "Reports":"Rapporti", "Audit":"Audit", "Settings":"Impostazioni", "New project":"Nuovo progetto", "Close":"Chiudi", "Cancel":"Annulla", "Refresh":"Aggiorna", "Language":"Lingua"},
    "pt": {"Dashboard":"Painel", "Projects":"Projetos", "Papers":"Artigos", "Sources":"Fontes", "Analysis":"Análise", "Reports":"Relatórios", "Audit":"Auditoria", "Settings":"Configurações", "New project":"Novo projeto", "Close":"Fechar", "Cancel":"Cancelar", "Refresh":"Atualizar", "Language":"Idioma"},
    "ja": {"Dashboard":"ダッシュボード", "Projects":"プロジェクト", "Papers":"論文", "Sources":"情報源", "Analysis":"分析", "Reports":"レポート", "Audit":"監査", "Settings":"設定", "New project":"新規プロジェクト", "Close":"閉じる", "Cancel":"キャンセル", "Refresh":"更新", "Language":"言語"},
    "zh": {"Dashboard":"仪表板", "Projects":"项目", "Papers":"论文", "Sources":"来源", "Analysis":"分析", "Reports":"报告", "Audit":"审计", "Settings":"设置", "New project":"新建项目", "Close":"关闭", "Cancel":"取消", "Refresh":"刷新", "Language":"语言"},
    "ko": {"Dashboard":"대시보드", "Projects":"프로젝트", "Papers":"논문", "Sources":"출처", "Analysis":"분석", "Reports":"보고서", "Audit":"감사", "Settings":"설정", "New project":"새 프로젝트", "Close":"닫기", "Cancel":"취소", "Refresh":"새로 고침", "Language":"언어"},
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

    def translate(self, context: str, source_text: str, disambiguation=None, n: int = -1) -> str:
        return self.catalog.get(source_text, "")


class LanguageManager(QObject):
    """Single application-wide localization service for legacy literal UI strings."""

    def __init__(self, application: QCoreApplication) -> None:
        super().__init__(application)
        self.application = application
        self.language = "en"
        self._translator: CatalogTranslator | None = None
        self._qt_translator: QTranslator | None = None
        self._source_cache: weakref.WeakKeyDictionary[QWidget, dict[str, object]] = weakref.WeakKeyDictionary()
        application.installEventFilter(self)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() in (QEvent.Type.Show, QEvent.Type.LanguageChange) and isinstance(obj, QWidget):
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
            self._translator = CatalogTranslator(_load_catalog(language), self.application)
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
        # QAction is owned by a QWidget hierarchy but is not itself a QWidget.
        key_name = f"_psi_i18n_{key}"
        source = action.property(key_name)
        if source is None:
            action.setProperty(key_name, value)
            return value
        return str(source)

    def _translate_widget(self, widget: QWidget) -> None:
        if isinstance(widget, (QLabel, QAbstractButton, QGroupBox)):
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
            sources = state.setdefault("items", [widget.itemText(i) for i in range(widget.count())])
            for index, source in enumerate(sources):
                if index < widget.count():
                    widget.setItemText(index, self.translate(str(source)))
        elif isinstance(widget, QListWidget):
            state = self._state(widget)
            sources = state.setdefault("items", [widget.item(i).text() for i in range(widget.count())])
            for index, source in enumerate(sources):
                if index < widget.count():
                    widget.item(index).setText(self.translate(str(source)))
        elif isinstance(widget, QTabWidget):
            state = self._state(widget)
            sources = state.setdefault("tabs", [widget.tabText(i) for i in range(widget.count())])
            for index, source in enumerate(sources):
                if index < widget.count():
                    widget.setTabText(index, self.translate(str(source)))
        elif isinstance(widget, QTableWidget):
            state = self._state(widget)
            sources = state.setdefault("headers", [widget.horizontalHeaderItem(i).text() if widget.horizontalHeaderItem(i) else "" for i in range(widget.columnCount())])
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
    selector.setCurrentIndex(next(i for i, (code, _) in enumerate(LANGUAGES) if code == manager.language))
    selector.currentIndexChanged.connect(lambda index: manager.set_language(str(selector.itemData(index))))
    sidebar = window.findChild(QWidget, "sidebar")
    if sidebar is not None and sidebar.layout() is not None:
        sidebar.layout().insertWidget(max(0, sidebar.layout().count() - 1), selector)
    manager.apply(window)
    return selector
