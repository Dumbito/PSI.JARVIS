from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton

from psi_jarvis.gui.ai_assistant import AIAssistantDialog
from psi_jarvis.gui.empty_state import EmptyState
from psi_jarvis.gui.toast import Toast


def test_empty_state_exposes_action(qtbot):
    called = []
    widget = EmptyState("No projects", "Create one.", "Create", lambda: called.append(True))
    qtbot.addWidget(widget)
    widget.show()
    button = widget.findChild(QPushButton)
    assert button is not None
    qtbot.mouseClick(button, Qt.MouseButton.LeftButton)
    assert called == [True]


def test_toast_is_non_modal_and_uses_no_graphics_effect(qtbot):
    parent = EmptyState("Parent", "Test")
    qtbot.addWidget(parent)
    parent.resize(500, 300)
    parent.show()
    toast = Toast.show_message(parent, "Saved", duration_ms=500)
    qtbot.addWidget(toast)
    assert toast.isVisible()
    assert toast.windowModality().value == 0
    assert toast.graphicsEffect() is None


def test_ai_assistant_rejects_request_without_paper_identity(qtbot, monkeypatch):
    monkeypatch.setattr("psi_jarvis.gui.ai_assistant.OllamaClient.list_models", lambda self: ("qwen3:8b",))
    dialog = AIAssistantDialog({"title": "Test paper", "abstract": "Abstract", "paper_id": ""})
    qtbot.addWidget(dialog)
    dialog.show()
    qtbot.waitUntil(lambda: dialog.models.count() == 1)
    dialog._ask()
    assert "identity is unavailable" in dialog.status.text()
