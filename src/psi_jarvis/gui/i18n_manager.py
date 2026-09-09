from __future__ import annotations

import json
import weakref
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QEvent, QLibraryInfo, QObject, QTranslator
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QAbstractButton, QComboBox, QGroupBox, QLabel, QLineEdit, QListWidget, QTableWidget, QTabWidget, QTextEdit, QWidget

LANGUAGES = (("en", "English"), ("es", "Español"), ("fr", "Français"), ("de", "Deutsch"), ("it", "Italiano"), ("pt", "Português"), ("ja", "日本語"), ("zh", "中文"), ("ko", "한국어"))
BUILTIN = {"es": {"Dashboard":"Panel", "Projects":"Proyectos", "Papers":"Artículos", "Sources":"Fuentes", "Screening":"Screening", "Analysis":"Análisis", "Reports":"Informes", "Audit":"Auditoría", "Settings":"Configuración", "New project":"Nuevo proyecto", "Close":"Cerrar", "Cancel":"Cancelar", "OK":"Aceptar", "Refresh":"Actualizar", "Overview":"Resumen", "Rules":"Reglas", "Exclusions":"Exclusiones", "Deduplication":"Deduplicación", "Authors":"Autores", "Journals":"Revistas", "Years":"Años", "Language":"Idioma", "Research question":"Pregunta de investigación", "General observations":"Observaciones generales", "Methodology":"Metodología", "Population":"Población", "Relevant results":"Resultados relevantes", "Possible exclusion criteria":"Posibles criterios de exclusión", "Scientific summary":"Resumen científico"}}


def _catalog_path(language: str) -> Path:
    return Path(__file__).resolve().parent / "translations" / f"ui_{language}.json"


def _load_catalog(language: str) -> dict[str, str]:
    catalog = dict(BUILTIN.get(language, {}))
    path = _catalog_path(language)
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                catalog.update({str(k): str(v) for k, v in data.items()})
        except (OSError, json.JSONDecodeError):
            pass
    return catalog


class CatalogTranslator(QTranslator):
    def __init__(self, catalog, parent=None):
        super().__init__(parent)
        self.catalog = catalog

    def translate(self, context, source_text, disambiguation=None, n=-1):
        return self.catalog.get(source_text, "")


class LanguageManager(QObject):
    """Single application-wide localization service for literal Qt UI text."""

    def __init__(self, application):
        super().__init__(application)
        self.application = application
        self.language = "en"
        self._translator = None
        self._qt_translator = None
        self._source_cache = weakref.WeakKeyDictionary()
        application.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() in (QEvent.Type.Show, QEvent.Type.LanguageChange) and isinstance(obj, QWidget):
            self.apply(obj)
        return False

    def set_language(self, language):
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
            self.apply(widget)

    def translate(self, text):
        return text if self.language == "en" else _load_catalog(self.language).get(text, text)

    def _state(self, widget):
        return self._source_cache.setdefault(widget, {})

    def _remember(self, widget, key, current):
        state = self._state(widget)
        if key not in state:
            state[key] = current
        return state[key]

    def apply(self, root):
        self._translate_widget(root)
        for child in root.findChildren(QWidget):
            self._translate_widget(child)
        if isinstance(root, QWidget):
            for action in root.findChildren(QAction):
                source = self._remember(action, "text", action.text())
                action.setText(self.translate(source))
                tip = self._remember(action, "tooltip", action.toolTip())
                if tip:
                    action.setToolTip(self.translate(tip))

    def _translate_widget(self, widget):
        window_title = widget.windowTitle()
        if window_title:
            source = self._remember(widget, "window_title", window_title)
            widget.setWindowTitle(self.translate(source))

        if isinstance(widget, (QLabel, QAbstractButton)):
            source = self._remember(widget, "text", widget.text())
            widget.setText(self.translate(source))
            self._translate_tooltip(widget)
        elif isinstance(widget, QGroupBox):
            source = self._remember(widget, "title", widget.title())
            widget.setTitle(self.translate(source))
            self._translate_tooltip(widget)
        elif isinstance(widget, (QLineEdit, QTextEdit)):
            source = self._remember(widget, "placeholder", widget.placeholderText())
            if source:
                widget.setPlaceholderText(self.translate(source))
        elif isinstance(widget, QComboBox):
            sources = self._state(widget).setdefault("items", [widget.itemText(i) for i in range(widget.count())])
            for i, source in enumerate(sources):
                if i < widget.count():
                    widget.setItemText(i, self.translate(str(source)))
        elif isinstance(widget, QListWidget):
            sources = self._state(widget).setdefault("items", [widget.item(i).text() for i in range(widget.count())])
            for i, source in enumerate(sources):
                if i < widget.count():
                    widget.item(i).setText(self.translate(str(source)))
        elif isinstance(widget, QTabWidget):
            sources = self._state(widget).setdefault("tabs", [widget.tabText(i) for i in range(widget.count())])
            for i, source in enumerate(sources):
                if i < widget.count():
                    widget.setTabText(i, self.translate(str(source)))
        elif isinstance(widget, QTableWidget):
            sources = self._state(widget).setdefault("headers", [widget.horizontalHeaderItem(i).text() if widget.horizontalHeaderItem(i) else "" for i in range(widget.columnCount())])
            for i, source in enumerate(sources):
                item = widget.horizontalHeaderItem(i)
                if item:
                    item.setText(self.translate(str(source)))

    def _translate_tooltip(self, widget):
        tip = self._remember(widget, "tooltip", widget.toolTip())
        if tip:
            widget.setToolTip(self.translate(tip))


def install_language_selector(window, manager):
    selector = QComboBox(window)
    selector.setObjectName("languageSelector")
    selector.setToolTip("Language")
    for code, name in LANGUAGES:
        selector.addItem(name, code)
    selector.currentIndexChanged.connect(lambda index: manager.set_language(str(selector.itemData(index))))
    sidebar = window.findChild(QWidget, "sidebar")
    if sidebar is not None and sidebar.layout() is not None:
        sidebar.layout().insertWidget(max(0, sidebar.layout().count() - 1), selector)
    manager.apply(window)
    return selector
