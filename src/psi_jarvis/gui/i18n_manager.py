from __future__ import annotations

import json
import re
import weakref
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
    ("en", "English"), ("es", "Español"), ("fr", "Français"),
    ("de", "Deutsch"), ("it", "Italiano"), ("pt", "Português"),
    ("ja", "日本語"), ("zh", "中文"), ("ko", "한국어"),
)

# Small deterministic fallback catalog. Full catalogs in translations/ui_*.json
# are merged on top of these values at runtime.
BUILTIN: dict[str, dict[str, str]] = {
    "es": {
        "Dashboard": "Panel", "Projects": "Proyectos", "Papers": "Artículos",
        "Sources": "Fuentes", "Screening": "Screening", "Analysis": "Análisis",
        "Reports": "Informes", "Audit": "Auditoría", "Settings": "Configuración",
        "New project": "Nuevo proyecto", "Paper details": "Detalles del artículo",
        "Screening evidence": "Evidencia del screening", "Decision": "Decisión",
        "Rule evidence": "Evidencia de reglas", "Close": "Cerrar", "Cancel": "Cancelar",
        "OK": "Aceptar", "Refresh": "Actualizar", "Overview": "Resumen",
        "Rules": "Reglas", "Exclusions": "Exclusiones", "Deduplication": "Deduplicación",
        "Authors": "Autores", "Journals": "Revistas", "Years": "Años", "Language": "Idioma",
        "Included": "Incluido", "Excluded": "Excluido", "All decisions": "Todas las decisiones",
        "All runs": "Todas las ejecuciones", "Research question": "Pregunta de investigación",
        "Methodology": "Metodología", "Population": "Población",
        "Relevant results": "Resultados relevantes", "Possible exclusion criteria": "Posibles criterios de exclusión",
        "Scientific summary": "Resumen científico", "General observations": "Observaciones generales",
    },
    "fr": {"Dashboard": "Tableau de bord", "Projects": "Projets", "Papers": "Articles", "Sources": "Sources", "Analysis": "Analyse", "Reports": "Rapports", "Audit": "Audit", "Settings": "Paramètres", "Close": "Fermer", "Cancel": "Annuler", "Refresh": "Actualiser", "Language": "Langue"},
    "de": {"Dashboard": "Übersicht", "Projects": "Projekte", "Papers": "Artikel", "Sources": "Quellen", "Analysis": "Analyse", "Reports": "Berichte", "Audit": "Audit", "Settings": "Einstellungen", "Close": "Schließen", "Cancel": "Abbrechen", "Refresh": "Aktualisieren", "Language": "Sprache"},
    "it": {"Dashboard": "Dashboard", "Projects": "Progetti", "Papers": "Articoli", "Sources": "Fonti", "Analysis": "Analisi", "Reports": "Rapporti", "Audit": "Audit", "Settings": "Impostazioni", "Close": "Chiudi", "Cancel": "Annulla", "Refresh": "Aggiorna", "Language": "Lingua"},
    "pt": {"Dashboard": "Painel", "Projects": "Projetos", "Papers": "Artigos", "Sources": "Fontes", "Analysis": "Análise", "Reports": "Relatórios", "Audit": "Auditoria", "Settings": "Configurações", "Close": "Fechar", "Cancel": "Cancelar", "Refresh": "Atualizar", "Language": "Idioma"},
    "ja": {"Dashboard": "ダッシュボード", "Projects": "プロジェクト", "Papers": "論文", "Sources": "情報源", "Analysis": "分析", "Reports": "レポート", "Audit": "監査", "Settings": "設定", "Close": "閉じる", "Cancel": "キャンセル", "Refresh": "更新", "Language": "言語"},
    "zh": {"Dashboard": "仪表板", "Projects": "项目", "Papers": "论文", "Sources": "来源", "Analysis": "分析", "Reports": "报告", "Audit": "审计", "Settings": "设置", "Close": "关闭", "Cancel": "取消", "Refresh": "刷新", "Language": "语言"},
    "ko": {"Dashboard": "대시보드", "Projects": "프로젝트", "Papers": "논문", "Sources": "출처", "Analysis": "분석", "Reports": "보고서", "Audit": "감사", "Settings": "설정", "Close": "닫기", "Cancel": "취소", "Refresh": "새로 고침", "Language": "언어"},
}

_PLACEHOLDER_RE = re.compile(r"\{[^{}]+\}")


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


def _translate_dynamic(text: str, catalog: dict[str, str]) -> str:
    translated = catalog.get(text)
    if translated is not None:
        return translated
    # Dynamic f-string templates are stored as complete templates by the
    # extractor. If an instantiated message is received, translate its
    # template while preserving runtime values.
    for template, target in catalog.items():
        if "{" not in template or "}" not in template:
            continue
        pattern = re.escape(template)
        pattern = _PLACEHOLDER_RE.sub(r"(.+?)", pattern)
        if re.fullmatch(pattern, text, flags=re.DOTALL):
            try:
                values = re.findall(r"(.+?)", text, flags=re.DOTALL)
                return target.format(*values)
            except (IndexError, KeyError, ValueError):
                return target
    return text


class CatalogTranslator(QTranslator):
    def __init__(self, catalog: dict[str, str], parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.catalog = catalog

    def translate(self, context: str, source_text: str, disambiguation=None, n: int = -1) -> str:
        return self.catalog.get(source_text, "")


class LanguageManager(QObject):
    """Application-wide localization service for the complete Qt widget tree."""

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
        if self._translator is not None:
            self.application.removeTranslator(self._translator)
            self._translator = None
        if self._qt_translator is not None:
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
        return _translate_dynamic(text, _load_catalog(self.language))

    def _state(self, widget: QWidget) -> dict[str, object]:
        state = self._source_cache.get(widget)
        if state is None:
            state = {}
            self._source_cache[widget] = state
        return state

    def _remember(self, widget: QWidget, key: str, value: str) -> str:
        state = self._state(widget)
        source_key = f"{key}_source"
        source = state.get(source_key)
        if source is None:
            state[source_key] = value
            return value
        return str(source)

    def _remember_action(self, action: QAction, key: str, value: str) -> str:
        key_name = f"_psi_i18n_{key}"
        source = action.property(key_name)
        if source is None:
            action.setProperty(key_name, value)
            return value
        return str(source)

    def _translate_widget(self, widget: QWidget) -> None:
        if isinstance(widget, (QLabel, QAbstractButton)):
            source = self._remember(widget, "text", widget.text())
            widget.setText(self.translate(source))
            tooltip = self._remember(widget, "tooltip", widget.toolTip())
            if tooltip:
                widget.setToolTip(self.translate(tooltip))
        elif isinstance(widget, QGroupBox):
            source = self._remember(widget, "title", widget.title())
            widget.setTitle(self.translate(source))
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
            headers = state.setdefault("headers", [widget.horizontalHeaderItem(i).text() if widget.horizontalHeaderItem(i) else "" for i in range(widget.columnCount())])
            for index, source in enumerate(headers):
                item = widget.horizontalHeaderItem(index)
                if item is not None:
                    item.setText(self.translate(str(source)))

        for action in widget.actions():
            text = self._remember_action(action, "text", action.text())
            action.setText(self.translate(text))
            tooltip = self._remember_action(action, "tooltip", action.toolTip())
            if tooltip:
                action.setToolTip(self.translate(tooltip))

    def apply(self, widget: QWidget) -> None:
        self._translate_widget(widget)
        for child in widget.findChildren(QWidget):
            self._translate_widget(child)
