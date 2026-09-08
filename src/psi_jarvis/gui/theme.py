from __future__ import annotations

from PySide6.QtCore import QEvent, QEasingCurve, QObject, QPoint, QPropertyAnimation, QTimer, Qt
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsOpacityEffect,
    QHeaderView,
    QPushButton,
    QStackedWidget,
    QTableWidget,
)


STYLE = """
QWidget { background: #0a111c; color: #dce7f5; font-family: Inter, Noto Sans, sans-serif; font-size: 13px; }
QMainWindow { background: #08101a; }
QLabel { background: transparent; }
QFrame#sidebar { background: #091522; border-right: 1px solid #1d3044; }
QLabel#brand { color: #f4f8ff; font-size: 19px; font-weight: 700; }
QLabel#version { color: #66809b; font-size: 11px; }
QLabel#tagline { color: #7188a4; font-size: 10px; }
QLabel#sidebarFooter { color: #7188a4; font-size: 10px; line-height: 1.35; }
QPushButton#nav { text-align: left; border: 0; border-left: 3px solid transparent; border-radius: 8px; padding: 10px 12px; color: #9eb2ca; background: transparent; }
QPushButton#nav:hover { background: #12253a; color: #edf5ff; }
QPushButton#nav[active="true"] { background: #15385d; color: #7fc0ff; border-left-color: #61b0ff; }
QPushButton#nav[active="true"]:hover { background: #194367; color: #8bc9ff; }
QLabel#pageTitle { font-size: 27px; font-weight: 700; color: #f1f6fc; }
QLabel#pageSubtitle { color: #8095ad; }
QLabel#dialogTitle { font-size: 20px; font-weight: 700; color: #f1f6fc; padding-bottom: 4px; }
QFrame#card { background: #0f1c2b; border: 1px solid #21374d; border-radius: 10px; }
QFrame#card:hover { background: #112235; border-color: #315776; }
QLabel#metricValue { font-size: 25px; font-weight: 700; color: #eef6ff; }
QLabel#metricLabel { color: #8da3bb; }
QLabel#metricAccent { color: #61b0ff; font-size: 11px; }
QLabel#sectionTitle { font-size: 15px; font-weight: 600; color: #eaf2fb; }
QLabel#tutorialEyebrow { color: #61b0ff; font-size: 11px; font-weight: 700; letter-spacing: 1px; }
QLabel#tutorialTitle { color: #f4f8ff; font-size: 28px; font-weight: 700; }
QLabel#tutorialBody { color: #a9bdd3; font-size: 15px; line-height: 1.5; }
QLabel#tutorialDestination { color: #61b0ff; font-size: 12px; font-weight: 600; }
QLabel#tutorialProgress { color: #7188a4; font-size: 11px; }
QProgressBar { background: #17273a; border: 0; border-radius: 6px; height: 12px; text-align: center; color: #dbeafe; }
QProgressBar::chunk { background: #4ba5ff; border-radius: 6px; min-width: 0px; }
QProgressBar[empty="true"]::chunk { background: transparent; }
QTableWidget, QListWidget, QTextEdit { background: #0c1826; alternate-background-color: #0f1e2f; border: 1px solid #21374d; gridline-color: #1a2c3f; border-radius: 8px; }
QHeaderView::section { background: #122235; color: #91a8c0; border: 0; padding: 9px; font-weight: 600; }
QTableWidget::item { padding: 7px; }
QTableWidget::item:hover, QListWidget::item:hover { background: #142b42; color: #edf5ff; }
QTableWidget::item:selected, QListWidget::item:selected { background: #1a426a; color: white; }
QListWidget::item { padding: 12px; border-radius: 6px; }
QPushButton { border: 1px solid transparent; border-radius: 7px; }
QPushButton:focus { border-color: #61b0ff; }
QPushButton#primary { background: #2685e8; color: white; border-color: #2685e8; padding: 9px 14px; font-weight: 600; }
QPushButton#primary:hover { background: #3a96f4; border-color: #3a96f4; }
QPushButton#primary:focus { border-color: #9bd4ff; }
QPushButton#secondary { background: #13253a; color: #b8c9db; border-color: #29415b; padding: 9px 14px; }
QPushButton#secondary:hover { background: #19304a; border-color: #3a5d7d; }
QPushButton#secondary:focus { border-color: #61b0ff; }
QPushButton:disabled { color: #50667e; background: #0d1926; border-color: #1a2b3d; }
QLineEdit, QComboBox { background: #0b1725; border: 1px solid #29405a; border-radius: 7px; padding: 8px; color: #dce7f5; }
QLineEdit:focus, QComboBox:focus { border: 1px solid #61b0ff; }
QComboBox QAbstractItemView { background: #0e1a29; color: #dce7f5; selection-background-color: #1a426a; }
QTabWidget::pane { border: 1px solid #21374d; border-radius: 8px; background: #0c1826; }
QTabBar::tab { background: #0d1927; color: #8198b1; padding: 9px 14px; border: 0; }
QTabBar::tab:selected { color: #eaf2fb; background: #15385d; }
QTabBar::tab:focus { border: 1px solid #61b0ff; }
QDialog { background: #0a111c; }
QMessageBox { background: #0a111c; }
QMessageBox QLabel { background: transparent; color: #dce7f5; }
QMessageBox QPushButton { min-width: 86px; padding: 8px 14px; background: #13253a; color: #dce7f5; border: 1px solid #29415b; }
QMessageBox QPushButton:hover { background: #19304a; border-color: #3a5d7d; }
QMessageBox QPushButton:focus { border-color: #61b0ff; }
QDialogButtonBox QPushButton { min-width: 86px; }
QScrollBar:vertical { background: #0a1521; width: 10px; margin: 0; }
QScrollBar::handle:vertical { background: #29415b; border-radius: 5px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #3a5d7d; }
QScrollBar:horizontal { background: #0a1521; height: 10px; margin: 0; }
QScrollBar::handle:horizontal { background: #29415b; border-radius: 5px; min-width: 30px; }
QScrollBar::handle:horizontal:hover { background: #3a5d7d; }
QScrollBar::add-line, QScrollBar::sub-line, QScrollBar::add-page, QScrollBar::sub-page { background: transparent; border: 0; }
QStatusBar { background: #08101a; color: #6f879f; border-top: 1px solid #1d3045; }
"""


class _UiAnimationFilter(QObject):
    """Subtle, non-blocking interaction animations shared by the GUI."""

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        event_type = event.type()
        if event_type == QEvent.Type.Show:
            self._on_show(watched)
        elif event_type == QEvent.Type.MouseMove and getattr(
            watched, "_psi_hover_hooked", False
        ):
            self._table_hover_move(watched, event.position().toPoint())
        elif event_type == QEvent.Type.Leave and getattr(
            watched, "_psi_hover_hooked", False
        ):
            self._table_hover_leave(watched)
        elif event_type == QEvent.Type.Resize and isinstance(watched, QTableWidget):
            self._configure_table(watched)
        return super().eventFilter(watched, event)

    def _on_show(self, watched: QObject) -> None:
        if isinstance(watched, QStackedWidget):
            self._watch_stack(watched)
        elif isinstance(watched, QTableWidget):
            self._configure_table(watched)
        elif isinstance(watched, QPushButton) and watched.text() == "Import & screen…":
            watched.setText("Import && screen…")

    def _watch_stack(self, stack: QStackedWidget) -> None:
        if getattr(stack, "_psi_animation_hooked", False):
            return
        stack._psi_animation_hooked = True
        stack.currentChanged.connect(
            lambda index, widget=stack: self._animate_stack_page(widget, index)
        )
        self._animate_stack_page(stack, stack.currentIndex())

    def _animate_stack_page(self, stack: QStackedWidget, index: int) -> None:
        if index < 0:
            return
        page = stack.widget(index)
        if page is not None:
            self._fade_in(page, 180)

    def _fade_in(self, widget: QObject, duration: int) -> None:
        if not hasattr(widget, "setGraphicsEffect"):
            return
        effect = getattr(widget, "_psi_opacity_effect", None)
        if effect is None:
            effect = QGraphicsOpacityEffect(widget)
            widget._psi_opacity_effect = effect
            widget.setGraphicsEffect(effect)
        animation = getattr(widget, "_psi_opacity_animation", None)
        if animation is not None:
            animation.stop()
        animation = QPropertyAnimation(effect, b"opacity", widget)
        animation.setDuration(duration)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        widget._psi_opacity_animation = animation
        animation.start()

    def _configure_table(self, table: QTableWidget) -> None:
        header = table.horizontalHeader()
        for section in range(header.count()):
            header.setSectionResizeMode(section, QHeaderView.ResizeMode.ResizeToContents)
        header.setStretchLastSection(True)
        viewport = table.viewport()
        viewport.setMouseTracking(True)
        if not getattr(viewport, "_psi_hover_hooked", False):
            viewport._psi_hover_hooked = True
            viewport.installEventFilter(self)
            overlay = QFrame(viewport)
            overlay.setObjectName("tableHoverOverlay")
            overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
            overlay.setStyleSheet(
                "QFrame#tableHoverOverlay { background: rgba(97, 176, 255, 0.045); "
                "border: 1px solid rgba(97, 176, 255, 0.16); border-radius: 4px; }"
            )
            overlay.hide()
            viewport._psi_hover_overlay = overlay
            viewport._psi_hover_animation = None

    def _table_hover_move(self, viewport: QObject, position: QPoint) -> None:
        table = viewport.parentWidget()
        if not isinstance(table, QTableWidget):
            return
        overlay = getattr(viewport, "_psi_hover_overlay", None)
        if overlay is None:
            return
        index = table.indexAt(position)
        if not index.isValid():
            self._table_hover_leave(viewport)
            return
        rect = table.visualRect(index)
        rect.setLeft(0)
        rect.setRight(viewport.width() - 1)
        if overlay.geometry() == rect and overlay.isVisible():
            return
        was_visible = overlay.isVisible()
        if not was_visible:
            overlay.setGeometry(rect)
            overlay.show()
            return
        animation = getattr(viewport, "_psi_hover_animation", None)
        if animation is not None:
            animation.stop()
        animation = QPropertyAnimation(overlay, b"geometry", overlay)
        animation.setDuration(120)
        animation.setStartValue(overlay.geometry())
        animation.setEndValue(rect)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        viewport._psi_hover_animation = animation
        animation.start()

    @staticmethod
    def _table_hover_leave(viewport: QObject) -> None:
        overlay = getattr(viewport, "_psi_hover_overlay", None)
        if overlay is None:
            return
        animation = getattr(viewport, "_psi_hover_animation", None)
        if animation is not None:
            animation.stop()
        overlay.hide()
        viewport._psi_hover_animation = None


_ANIMATION_FILTER: _UiAnimationFilter | None = None


def apply_theme(app: QApplication) -> None:
    global _ANIMATION_FILTER
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE)
    if _ANIMATION_FILTER is None:
        _ANIMATION_FILTER = _UiAnimationFilter(app)
        app.installEventFilter(_ANIMATION_FILTER)

    for widget in app.allWidgets():
        if isinstance(widget, QTableWidget):
            _ANIMATION_FILTER._configure_table(widget)
        if isinstance(widget, QPushButton) and widget.text() == "Import & screen…":
            widget.setText("Import && screen…")
