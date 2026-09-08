from __future__ import annotations

import hashlib

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QComboBox, QDialog, QDialogButtonBox, QLabel, QPushButton, QTextEdit, QVBoxLayout

from psi_jarvis.domain.ai.assistance import AIAssistanceRequest, AIAssistanceSuggestion
from psi_jarvis.infrastructure.ollama_client import OllamaClient, OllamaError

PROMPT_VERSION = "assistant-v1"


class _AssistantWorker(QThread):
    succeeded = Signal(object)
    failed = Signal(str)

    def __init__(self, client: OllamaClient, request: AIAssistanceRequest) -> None:
        super().__init__()
        self.client = client
        self.request = request

    def run(self) -> None:
        try:
            self.succeeded.emit(self.client.generate(self.request))
        except OllamaError as exc:
            self.failed.emit(str(exc))
        except Exception as exc:
            self.failed.emit(f"AI assistant failed: {exc}")


class _ModelWorker(QThread):
    succeeded = Signal(object)
    failed = Signal(str)

    def __init__(self, client: OllamaClient) -> None:
        super().__init__()
        self.client = client

    def run(self) -> None:
        try:
            self.succeeded.emit(self.client.list_models())
        except OllamaError as exc:
            self.failed.emit(str(exc))
        except Exception as exc:
            self.failed.emit(f"AI assistant failed: {exc}")


class AIAssistantDialog(QDialog):
    """Human-review assistant UI; it never edits scientific decisions."""

    def __init__(self, details: dict, parent=None) -> None:
        super().__init__(parent)
        self.details = details
        self.client = OllamaClient()
        self.worker: _AssistantWorker | None = None
        self.model_worker: _ModelWorker | None = None
        self.setWindowTitle("Local AI assistant")
        self.resize(760, 560)
        root = QVBoxLayout(self)
        root.addWidget(QLabel("Auxiliary local analysis · scientific decisions remain deterministic."))
        root.addWidget(QLabel(f"Paper: {details.get('title') or 'Untitled paper'}"))
        self.models = QComboBox()
        self.models.addItem("Select a local Ollama model…")
        root.addWidget(self.models)
        refresh = QPushButton("Refresh local models")
        refresh.clicked.connect(self._refresh_models)
        root.addWidget(refresh)
        self.ask = QPushButton("Ask AI for auxiliary observations")
        self.ask.setEnabled(False)
        self.ask.clicked.connect(self._ask)
        root.addWidget(self.ask)
        self.status = QLabel("Checking local Ollama models…")
        self.status.setObjectName("pageSubtitle")
        self.status.setWordWrap(True)
        root.addWidget(self.status)
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setPlaceholderText("The assistant response will appear here and is not a screening decision.")
        root.addWidget(self.output, 1)
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)
        self._refresh_models()

    def _refresh_models(self) -> None:
        if self.model_worker is not None and self.model_worker.isRunning():
            return
        self.models.setEnabled(False)
        self.ask.setEnabled(False)
        self.status.setText("Checking local Ollama models…")
        self.model_worker = _ModelWorker(self.client)
        self.model_worker.succeeded.connect(self._models_success)
        self.model_worker.failed.connect(self._models_failure)
        self.model_worker.finished.connect(self._model_worker_finished)
        self.model_worker.start()

    def _models_success(self, names) -> None:
        self.models.clear()
        self.models.addItems(names)
        self.ask.setEnabled(bool(names))
        self.status.setText(f"{len(names)} local model(s) available. Output is auxiliary evidence only.")

    def _models_failure(self, message: str) -> None:
        self.models.clear()
        self.models.addItem("No local model available")
        self.ask.setEnabled(False)
        self.status.setText(message)

    def _model_worker_finished(self) -> None:
        self.models.setEnabled(True)
        self.model_worker = None

    def _ask(self) -> None:
        if self.worker is not None and self.worker.isRunning():
            return
        model = self.models.currentText().strip()
        title = str(self.details.get("title") or "")
        abstract = str(self.details.get("abstract") or "")
        paper_id = str(self.details.get("paper_id") or "")
        if not model or model.startswith("Select ") or model.startswith("No local"):
            self.status.setText("Select an available local Ollama model first.")
            return
        if not paper_id:
            self.status.setText("Paper identity is unavailable; the assistant request was not sent.")
            return
        digest = hashlib.sha256(f"{title}\n{abstract}".encode("utf-8")).hexdigest()
        request = AIAssistanceRequest(
            paper_id=paper_id,
            title=title,
            abstract=abstract,
            model=model,
            prompt_version=PROMPT_VERSION,
            input_hash=digest,
        )
        self.output.clear()
        self.ask.setEnabled(False)
        self.status.setText("Generating auxiliary observations locally…")
        self.worker = _AssistantWorker(self.client, request)
        self.worker.succeeded.connect(self._success)
        self.worker.failed.connect(self._failure)
        self.worker.finished.connect(self._worker_finished)
        self.worker.start()

    def _success(self, suggestion: AIAssistanceSuggestion) -> None:
        self.output.setPlainText(suggestion.output)
        self.status.setText(
            f"Auxiliary suggestion · model {suggestion.model} · prompt {suggestion.prompt_version} · authority: {suggestion.authority}"
        )

    def _failure(self, message: str) -> None:
        self.status.setText(message)

    def _worker_finished(self) -> None:
        self.ask.setEnabled(self.models.count() > 0 and not self.models.currentText().startswith("No local"))
        self.worker = None

    def closeEvent(self, event) -> None:
        if (self.worker is not None and self.worker.isRunning()) or (
            self.model_worker is not None and self.model_worker.isRunning()
        ):
            event.ignore()
            self.status.setText("Wait for the local AI request to finish before closing this dialog.")
            return
        super().closeEvent(event)
