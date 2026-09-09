from __future__ import annotations

import pytest
from PySide6.QtWidgets import QDialog, QStackedWidget, QTabWidget, QTableWidget, QWidget

from psi_jarvis.gui.theme import _UiAnimationFilter


@pytest.fixture
def qt_app(qapp):
    # Keep these focused animation tests independent from Qt's global stylesheet
    # parser. The stylesheet is exercised by the application itself; these
    # tests only need the event-filter behavior under test.
    animation_filter = _UiAnimationFilter(qapp)
    qapp.installEventFilter(animation_filter)
    qapp._psi_test_animation_filter = animation_filter
    return qapp


def test_theme_does_not_install_graphics_effects_on_pages(qt_app):
    stack = QStackedWidget()
    stack.addWidget(QWidget())
    stack.addWidget(QWidget())
    stack.show()
    qt_app.processEvents()

    assert stack.currentWidget() is stack.widget(0)
    assert stack.currentWidget().graphicsEffect() is None

    stack.setCurrentIndex(1)
    qt_app.processEvents()
    assert stack.currentWidget() is stack.widget(1)
    assert stack.currentWidget().graphicsEffect() is None
    stack.close()


def test_tab_internal_stack_is_not_animated_as_a_main_stack(qt_app):
    tabs = QTabWidget()
    tabs.addTab(QWidget(), "Overview")
    tabs.addTab(QWidget(), "Rules")
    tabs.show()
    qt_app.processEvents()

    internal_stacks = tabs.findChildren(QStackedWidget)
    assert internal_stacks
    assert all(not getattr(stack, "_psi_animation_hooked", False) for stack in internal_stacks)
    tabs.close()


def test_tab_pages_use_position_animation_without_graphics_effect(qt_app):
    tabs = QTabWidget()
    first = QWidget()
    second = QWidget()
    tabs.addTab(first, "Overview")
    tabs.addTab(second, "Rules")
    tabs.show()
    qt_app.processEvents()

    tabs.setCurrentIndex(1)
    qt_app.processEvents()

    assert second.graphicsEffect() is None
    assert hasattr(second, "_psi_slide_animation")
    tabs.close()


def test_table_hover_overlay_is_not_a_graphics_effect(qt_app):
    table = QTableWidget(2, 2)
    table.setHorizontalHeaderLabels(["A", "B"])
    table.show()
    qt_app.processEvents()

    overlay = getattr(table.viewport(), "_psi_hover_overlay")
    assert overlay is not None
    assert overlay.graphicsEffect() is None
    table.close()


def test_dialog_animation_uses_geometry_only(qt_app):
    dialog = QDialog()
    dialog.resize(320, 180)
    dialog.show()
    qt_app.processEvents()

    assert hasattr(dialog, "_psi_dialog_animation")
    assert dialog.graphicsEffect() is None
    dialog.close()


def test_animation_filter_is_qobject_owned_by_application(qt_app):
    filters = [obj for obj in qt_app.children() if isinstance(obj, _UiAnimationFilter)]
    assert len(filters) == 1
