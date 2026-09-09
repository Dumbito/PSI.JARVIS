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
    ("Observaciones generales", "Identifica observaciones relevantes del artículo sin emitir una decisión de screening."),
    ("PICO", "Extrae Población/Problema, Intervención/Exposición, Comparador y Outcomes si están explícitos o razonablemente identificables. Marca como no informado lo que no aparezca."),
    ("Metodología", "Resume diseño, población, métodos, variables, intervención/exposición, comparador y análisis estadístico cuando estén descritos."),
    ("Población", "Caracteriza la población estudiada, tamaño muestral, criterios relevantes y contexto. No inventes datos ausentes."),
    ("Resultados relevantes", "Resume únicamente resultados que estén presentes en el texto proporcionado. Distingue resultados de conclusiones."),
    ("Posibles criterios de exclusión", "Compara el artículo de forma orientativa con los criterios del proyecto si están disponibles, explicando qué evidencia apoya o contradice cada punto. No decidas excluirlo."),
    ("Resumen científico", "Produce un resumen estructurado y fiel del título y abstract, señalando limitaciones de información."),
)


def _build_prompt(mode: str, task: str, title: str, abstract: str, criteria: str) -> str:
    return f"""Eres JARVIS, un agente auxiliar de análisis científico dentro de PSI.JARVIS.

REGLAS OBLIGATORIAS:
- Responde en español.
- Trabaja exclusivamente con la información proporcionada.
- No inventes datos, resultados, criterios ni referencias.
- No emitas una decisión final de inclusión/exclusión.
- No modifiques ni sugieras modificar silenciosamente ninguna decisión científica persistida.
- Diferencia claramente evidencia textual, inferencia prudente y ausencia de información.
- Si la información es insuficiente, dilo explícitamente.

MODO: {mode}
OBJETIVO: {task}

CRITERIOS DEL PROYECTO (si están disponibles):
{criteria or 'No proporcionados.'}

TÍTULO:
{title or 'No informado.'}

ABSTRACT:
{abstract or 'No hay abstract almacenado.'}

Entrega una respuesta estructurada, concisa y útil para un investigador humano. Termina con una sección 'Límite de la asistencia' indicando que la salida no es una decisión de screening."""


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
            self.failed.emit(f"Error del agente IA: {exc}")


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
            self.failed.emit(f"Error al consultar Ollama: {exc}")


class AIAssistantDialog(QDialog):
    """Agente IA local para asistencia científica; nunca edita decisiones."""

    def __init__(self, details: dict, parent=None) -> None:
        super().__init__(parent)
        self.details = details
        self.client = OllamaClient()
        self.worker: _AssistantWorker | None = None
        self.model_worker: _ModelWorker | None = None
        self.setWindowTitle("JARVIS · Agente IA local")
        self.resize(820, 680)

        root = QVBoxLayout(self)
        heading = QLabel("JARVIS · Agente IA local")
        heading.setObjectName("dialogTitle")
        root.addWidget(heading)
        note = QLabel(
            "Asistencia científica auxiliar mediante Ollama. JARVIS no sustituye al ScreeningEngine ni modifica decisiones persistidas."
        )
        note.setWordWrap(True)
        note.setObjectName("pageSubtitle")
        root.addWidget(note)
        root.addWidget(QLabel(f"Artículo: {details.get('title') or 'Sin título'}"))

        root.addWidget(QLabel("Modelo local"))
        model_row = QHBoxLayout()
        self.models = QComboBox()
        self.models.addItem("Selecciona un modelo local…")
        model_row.addWidget(self.models, 1)
        refresh = QPushButton("Actualizar modelos")
        refresh.clicked.connect(self._refresh_models)
        model_row.addWidget(refresh)
        root.addLayout(model_row)

        root.addWidget(QLabel("Modo de análisis"))
        self.mode = QComboBox()
        for name, _ in MODES:
            self.mode.addItem(name)
        root.addWidget(self.mode)

        root.addWidget(QLabel("Instrucción adicional (opcional)"))
        self.task = QLineEditCompat()
        self.task.setPlaceholderText("Ej.: céntrate en la población y los outcomes…")
        root.addWidget(self.task)

        self.ask = QPushButton("🤖 Analizar con JARVIS")
        self.ask.setEnabled(False)
        self.ask.setToolTip("Ejecuta el análisis local sin alterar el screening científico.")
        self.ask.clicked.connect(self._ask)
        root.addWidget(self.ask)

        self.status = QLabel("Comprobando modelos locales de Ollama…")
        self.status.setObjectName("pageSubtitle")
        self.status.setWordWrap(True)
        root.addWidget(self.status)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setPlaceholderText("La respuesta de JARVIS aparecerá aquí como asistencia auxiliar.")
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
        self.status.setText("Comprobando modelos locales de Ollama…")
        self.model_worker = _ModelWorker(self.client)
        self.model_worker.succeeded.connect(self._models_success)
        self.model_worker.failed.connect(self._models_failure)
        self.model_worker.finished.connect(self._model_worker_finished)
        self.model_worker.start()

    def _models_success(self, names) -> None:
        self.models.clear()
        self.models.addItems(names)
        self.ask.setEnabled(bool(names))
        self.status.setText(f"{len(names)} modelo(s) local(es) disponible(s). La IA es solo auxiliar.")

    def _models_failure(self, message: str) -> None:
        self.models.clear()
        self.models.addItem("No hay modelos locales disponibles")
        self.ask.setEnabled(False)
        self.status.setText(f"Ollama no está disponible: {message}")

    def _model_worker_finished(self) -> None:
        self.models.setEnabled(True)
        self.model_worker = None

    def _ask(self) -> None:
        if self.worker is not None and self.worker.isRunning():
            return
        model = self.models.currentText().strip()
        if not model or model.startswith("Selecciona") or model.startswith("No hay"):
            self.status.setText("Selecciona un modelo local disponible primero.")
            return
        paper_id = str(self.details.get("paper_id") or "")
        if not paper_id:
            self.status.setText("No se dispone de una identidad estable del artículo; no se envió la solicitud.")
            return

        title = str(self.details.get("title") or "")
        abstract = str(self.details.get("abstract") or "")
        criteria = str(self.details.get("criteria") or "")
        mode, mode_task = MODES[self.mode.currentIndex()]
        extra = self.task.text().strip()
        task = f"{mode_task}\n\nInstrucción adicional: {extra or 'Ninguna.'}"
        prompt = _build_prompt(mode, task, title, abstract, criteria)
        digest = hashlib.sha256(f"{title}\n{abstract}\n{criteria}".encode("utf-8")).hexdigest()
        request = AIAssistanceRequest(
            paper_id=paper_id,
            title=title,
            abstract=f"{prompt}\n\nFuente para el modelo:\n{abstract}",
            model=model,
            prompt_version=PROMPT_VERSION,
            input_hash=digest,
        )
        self.output.clear()
        self.ask.setEnabled(False)
        self.status.setText("JARVIS está analizando localmente…")
        self.worker = _AssistantWorker(self.client, request)
        self.worker.succeeded.connect(self._success)
        self.worker.failed.connect(self._failure)
        self.worker.finished.connect(self._worker_finished)
        self.worker.start()

    def _success(self, suggestion: AIAssistanceSuggestion) -> None:
        self.output.setPlainText(suggestion.output)
        self.status.setText(
            f"Asistencia auxiliar · modelo: {suggestion.model} · prompt: {suggestion.prompt_version} · autoridad: {suggestion.authority}"
        )

    def _failure(self, message: str) -> None:
        self.status.setText(message)

    def _worker_finished(self) -> None:
        self.ask.setEnabled(self.models.count() > 0 and not self.models.currentText().startswith("No hay"))
        self.worker = None

    def closeEvent(self, event) -> None:
        if (self.worker is not None and self.worker.isRunning()) or (
            self.model_worker is not None and self.model_worker.isRunning()
        ):
            event.ignore()
            self.status.setText("Espera a que termine la solicitud local antes de cerrar este diálogo.")
            return
        super().closeEvent(event)


class QLineEditCompat(QTextEdit):
    """Small single-line editor without adding another Qt import to the dialog."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedHeight(34)

    def text(self) -> str:
        return self.toPlainText().strip().replace("\n", " ")

    def setText(self, value: str) -> None:
        self.setPlainText(value)
