from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QLabel, QListWidget, QPushButton, QTabWidget, QWidget

TRANSLATIONS = {
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
    "Import & screen": "Importar y hacer screening",
    "Import & screen complete": "Importación y screening completados",
    "Review project": "Proyecto de revisión",
    "Browse…": "Explorar…",
    "Choose bibliographic file": "Seleccionar archivo bibliográfico",
    "Project name": "Nombre del proyecto",
    "Research question": "Pregunta de investigación",
    "Topic (required)": "Tema (obligatorio)",
    "Inclusion rules (one per line)": "Criterios de inclusión (uno por línea)",
    "Exclusion rules (one per line)": "Criterios de exclusión (uno por línea)",
    "Refresh PRISMA": "Actualizar PRISMA",
    "Refresh sources": "Actualizar fuentes",
    "All decisions": "Todas las decisiones",
    "Included": "Incluido",
    "Excluded": "Excluido",
    "All runs": "Todas las ejecuciones",
    "Refresh": "Actualizar",
    "Overview": "Resumen",
    "Rules": "Reglas",
    "Exclusions": "Exclusiones",
    "Deduplication": "Deduplicación",
    "Authors": "Autores",
    "Journals": "Revistas",
    "Years": "Años",
    "Export report…": "Exportar informe…",
    "No persisted screening runs recorded yet.": "Todavía no hay ejecuciones de screening persistidas.",
}


def tr(text: str) -> str:
    return TRANSLATIONS.get(text.strip(), text)


def apply_spanish_ui(root: QWidget) -> None:
    """Translate the current presentation tree without changing domain semantics."""
    for widget in root.findChildren(QWidget):
        if isinstance(widget, (QLabel, QPushButton)):
            text = widget.text()
            translated = tr(text)
            if translated == text and isinstance(widget, QPushButton):
                stripped = text.strip()
                for english, spanish in TRANSLATIONS.items():
                    if stripped.endswith(english) and stripped != english:
                        translated = text[: len(text) - len(english)] + spanish
                        break
            widget.setText(translated)
        elif isinstance(widget, QComboBox):
            for index in range(widget.count()):
                widget.setItemText(index, tr(widget.itemText(index)))
        elif isinstance(widget, QListWidget):
            for index in range(widget.count()):
                item = widget.item(index)
                item.setText(tr(item.text()))
        elif isinstance(widget, QTabWidget):
            for index in range(widget.count()):
                widget.setTabText(index, tr(widget.tabText(index)))

    if hasattr(root, "setWindowTitle"):
        root.setWindowTitle(tr(root.windowTitle()))
