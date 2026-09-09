from __future__ import annotations

import hashlib

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from psi_jarvis.domain.ai.assistance import AIAssistanceRequest, AIAssistanceSuggestion
from psi_jarvis.infrastructure.ollama_client import OllamaClient, OllamaError

PROMPT_VERSION = "jarvis-agent-v2-es"

MODES: tuple[tuple[str, str], ...] = (
    (
        "General observations",
        "Identify relevant observations from the paper without making a screening decision.",
    ),
    (
        "PICO",
        "Extract Population/Problem, Intervention/Exposure, Comparator and Outcomes when explicit or reasonably identifiable. Mark information that is not reported.",
    ),
    (
        "Methodology",
        "Summarize study design, population, methods, variables, intervention/exposure, comparator and statistical analysis when described.",
    ),
    (
        "Population",
        "Characterize the study population, sample size, relevant criteria and context. Do not invent missing data.",
    ),
    (
        "Relevant results",
        "Summarize only results present in the supplied text. Distinguish results from conclusions.",
    ),
    (
        "Possible exclusion criteria",
        "Compare the paper orientatively with project criteria when available, explaining evidence supporting or contradicting each point. Do not decide to exclude it.",
    ),
    (
        "Scientific summary",
        "Produce a structured, faithful summary of the title and abstract, noting information limitations.",
    ),
)


def _build_prompt(
    mode: str, task: str, title: str, abstract: str, criteria: str
) -> str:
    return f"""You are JARVIS, an auxiliary scientific-analysis agent inside PSI.JARVIS.

MANDATORY RULES:
- Respond in Spanish.
- Work exclusively with the information provided.
- Do not invent data, results, criteria or references.
- Do not issue a final inclusion/exclusion decision.
- Do not modify or silently suggest modifying any persisted scientific decision.
- Clearly distinguish textual evidence, cautious inference and missing information.
- If information is insufficient, state it explicitly.

MODE: {mode}
OBJECTIVE: {task}

PROJECT CRITERIA (if available):
{criteria or "Not provided."}

TITLE:
{title or "Not reported."}

ABSTRACT:
{abstract or "No abstract stored."}

Provide a structured, concise response useful to a human researcher. End with a section 'Límite de la asistencia' stating that the output is not a screening decision."""


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
            self.failed.emit(f"AI agent error: {exc}")


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
            self.failed.emit(f"Error while querying Ollama: {exc}")


class AIAssistantDialog(QDialog):
    """Local AI assistant for scientific support; it never edits decisions."""

    def __init__(self, details: dict, parent=None) -> None:
        super().__init__(parent)
        self.details = details
        self.client = OllamaClient()
        self.worker: _AssistantWorker | None = None
        self.model_worker: _ModelWorker | None = None
        self.setWindowTitle("JARVIS · Local AI assistant")
        self.resize(820, 680)

        root = QVBoxLayout(self)
        heading = QLabel("JARVIS · Local AI assistant")
        heading.setObjectName("dialogTitle")
        root.addWidget(heading)
        note = QLabel(
            "Auxiliary scientific assistance through Ollama. JARVIS does not replace ScreeningEngine or modify persisted decisions."
        )
        note.setWordWrap(True)
        note.setObjectName("pageSubtitle")
        root.addWidget(note)
        root.addWidget(QLabel(f"Paper: {details.get('title') or 'Untitled'}"))

        root.addWidget(QLabel("Local model"))
        model_row = QHBoxLayout()
        self.models = QComboBox()
        self.models.addItem("Select a local model…")
        model_row.addWidget(self.models, 1)
        refresh = QPushButton("Refresh models")
        refresh.clicked.connect(self._refresh_models)
        model_row.addWidget(refresh)
        root.addLayout(model_row)

        root.addWidget(QLabel("Analysis mode"))
        self.mode = QComboBox()
        for name, _ in MODES:
            self.mode.addItem(name)
        root.addWidget(self.mode)

        root.addWidget(QLabel("Additional instruction (optional)"))
        self.task = QLineEditCompat()
        self.task.setPlaceholderText("e.g. focus on the population and outcomes…")
        root.addWidget(self.task)

        self.ask = QPushButton("🤖 Analyze with JARVIS")
        self.ask.setEnabled(False)
        self.ask.setToolTip("Run local analysis without altering scientific screening.")
        self.ask.clicked.connect(self._ask)
        root.addWidget(self.ask)

        self.status = QLabel("Checking local Ollama models…")
        self.status.setObjectName("pageSubtitle")
        self.status.setWordWrap(True)
        root.addWidget(self.status)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setPlaceholderText(
            "JARVIS's response will appear here as auxiliary assistance."
        )
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
        self.status.setText(
            f"{len(names)} local model(s) available. AI is auxiliary only."
        )

    def _models_failure(self, message: str) -> None:
        self.models.clear()
        self.models.addItem("No local models available")
        self.ask.setEnabled(False)
        self.status.setText(f"Ollama is unavailable: {message}")

    def _model_worker_finished(self) -> None:
        self.models.setEnabled(True)
        self.model_worker = None

    def _ask(self) -> None:
        if self.worker is not None and self.worker.isRunning():
            return
        model = self.models.currentText().strip()
        if not model or model.startswith(("Select", "No local")):
            self.status.setText("Select an available local model first.")
            return
        paper_id = str(self.details.get("paper_id") or "")
        if not paper_id:
            self.status.setText(
                "No stable paper identity is available; the request was not sent."
            )
            return
        title = str(self.details.get("title") or "")
        abstract = str(self.details.get("abstract") or "")
        criteria = str(self.details.get("criteria") or "")
        mode, mode_task = MODES[self.mode.currentIndex()]
        extra = self.task.text().strip()
        task = f"{mode_task}\n\nAdditional instruction: {extra or 'None.'}"
        prompt = _build_prompt(mode, task, title, abstract, criteria)
        digest = hashlib.sha256(f"{title}\n{abstract}\n{criteria}".encode()).hexdigest()
        request = AIAssistanceRequest(
            paper_id=paper_id,
            title=title,
            abstract=f"{prompt}\n\nSource for model:\n{abstract}",
            model=model,
            prompt_version=PROMPT_VERSION,
            input_hash=digest,
        )
        self.output.clear()
        self.ask.setEnabled(False)
        self.status.setText("JARVIS is analyzing locally…")
        self.worker = _AssistantWorker(self.client, request)
        self.worker.succeeded.connect(self._success)
        self.worker.failed.connect(self._failure)
        self.worker.finished.connect(self._worker_finished)
        self.worker.start()

    def _success(self, suggestion: AIAssistanceSuggestion) -> None:
        self.output.setPlainText(suggestion.output)
        self.status.setText(
            f"Auxiliary assistance · model: {suggestion.model} · prompt: {suggestion.prompt_version} · authority: {suggestion.authority}"
        )

    def _failure(self, message: str) -> None:
        self.status.setText(message)

    def _worker_finished(self) -> None:
        self.ask.setEnabled(
            self.models.count() > 0
            and not self.models.currentText().startswith("No local")
        )
        self.worker = None

    def closeEvent(self, event) -> None:
        if (self.worker is not None and self.worker.isRunning()) or (
            self.model_worker is not None and self.model_worker.isRunning()
        ):
            event.ignore()
            self.status.setText(
                "Wait for the local request to finish before closing this dialog."
            )
            return
        super().closeEvent(event)


class QLineEditCompat(QTextEdit):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedHeight(34)

    def text(self) -> str:
        return self.toPlainText().strip().replace("\n", " ")

    def setText(self, value: str) -> None:
        self.setPlainText(value)
