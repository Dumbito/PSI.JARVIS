from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from PySide6.QtCore import QThread, Signal, QObject
from PySide6.QtWidgets import QComboBox, QDialog, QDialogButtonBox, QLabel, QProgressBar, QPushButton, QVBoxLayout, QWidget

from psi_jarvis.gui.i18n_manager import LANGUAGES, _catalog_path

GUI_ROOT = Path(__file__).resolve().parent
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
DEFAULT_MODEL = "qwen3:8b"

_SKIP_EXACT = {"", "__main__", "utf-8", "utf8"}
_CODE_RE = re.compile(r"^(?:[A-Za-z_][A-Za-z0-9_]*\.)+[A-Za-z_][A-Za-z0-9_]*$|^https?://|^#[0-9A-Fa-f]{3,8}$")


def _candidate(value: str) -> bool:
    value = value.strip()
    if value in _SKIP_EXACT or len(value) > 1200:
        return False
    if _CODE_RE.match(value) or value.startswith(("/", "--", "\\")):
        return False
    if value.endswith((".py", ".json", ".csv", ".xlsx", ".ris")):
        return False
    return any(ch.isalpha() for ch in value)


def extract_gui_strings() -> list[str]:
    """Extract literal user-facing GUI strings without hard-coding widget names."""
    found: set[str] = set()
    for path in GUI_ROOT.glob("*.py"):
        if path.name == Path(__file__).name:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and _candidate(node.value):
                found.add(node.value)
            elif isinstance(node, ast.JoinedStr):
                for part in node.values:
                    if isinstance(part, ast.Constant) and isinstance(part.value, str) and _candidate(part.value):
                        found.add(part.value)
    return sorted(found, key=lambda value: (value.lower(), value))


def _load_catalog(language: str) -> dict[str, str]:
    path = _catalog_path(language)
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return {str(key): str(value) for key, value in payload.items()} if isinstance(payload, dict) else {}


def _ollama_translate(model: str, language_name: str, entries: list[str], base_url: str) -> dict[str, str]:
    numbered = {str(index): value for index, value in enumerate(entries)}
    prompt = (
        "You translate a scientific desktop application's UI. Return ONLY a valid JSON object mapping each numeric ID "
        "to its translation. Preserve technical product names such as PSI.JARVIS, Ollama, ScreeningEngine, PRISMA, "
        "CSV, Excel, RIS, JSON and Markdown. Preserve placeholders like {0}, {step.page}, punctuation and line breaks. "
        f"Translate into {language_name}. Do not add commentary.\n\nINPUT:\n{json.dumps(numbered, ensure_ascii=False)}"
    )
    request = Request(
        base_url,
        data=json.dumps({"model": model, "prompt": prompt, "stream": False, "format": "json"}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=300) as response:
        payload = json.loads(response.read().decode("utf-8"))
    result = json.loads(str(payload.get("response", "{}")))
    if not isinstance(result, dict):
        raise ValueError("Ollama returned a non-object translation payload")
    return {entries[int(key)]: str(value) for key, value in result.items() if str(key).isdigit() and int(key) < len(entries)}


class TranslationWorker(QThread):
    progress = Signal(int, int, str)
    completed = Signal(str, int)
    failed = Signal(str)

    def __init__(self, language: str, model: str, base_url: str = OLLAMA_URL, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.language = language
        self.model = model
        self.base_url = base_url.rstrip("/") + "/api/generate" if not base_url.endswith("/api/generate") else base_url

    def run(self) -> None:
        try:
            entries = extract_gui_strings()
            existing = _load_catalog(self.language)
            missing = [entry for entry in entries if entry not in existing]
            if not missing:
                self.completed.emit(self.language, 0)
                return
            translated: dict[str, str] = {}
            batch_size = 25
            for start in range(0, len(missing), batch_size):
                if self.isInterruptionRequested():
                    return
                batch = missing[start : start + batch_size]
                translated.update(_ollama_translate(self.model, dict(LANGUAGES)[self.language], batch, self.base_url))
                self.progress.emit(min(start + len(batch), len(missing)), len(missing), self.language)
            existing.update(translated)
            path = _catalog_path(self.language)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(existing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            self.completed.emit(self.language, len(translated))
        except (OSError, URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
            self.failed.emit(f"{self.language}: {exc}")


class TranslationDialog(QDialog):
    """Generate/update complete GUI catalogs through a local Ollama model."""

    def __init__(self, manager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.manager = manager
        self.worker: TranslationWorker | None = None
        self.setWindowTitle("PSI.JARVIS · Translation catalogs")
        self.resize(520, 250)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Generate or update the full GUI translation catalog with a local Ollama model."))
        self.language = QComboBox()
        for code, name in LANGUAGES:
            if code != "en":
                self.language.addItem(name, code)
        layout.addWidget(self.language)
        self.model = QComboBox()
        self.model.setEditable(True)
        self.model.addItem(DEFAULT_MODEL)
        layout.addWidget(self.model)
        self.status = QLabel("Select a language and start generation.")
        layout.addWidget(self.status)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        layout.addWidget(self.progress)
        self.generate = QPushButton("Generate / update translations")
        self.generate.clicked.connect(self.start)
        layout.addWidget(self.generate)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.close)
        layout.addWidget(buttons)

    def start(self) -> None:
        if self.worker and self.worker.isRunning():
            return
        code = str(self.language.currentData())
        model = self.model.currentText().strip() or DEFAULT_MODEL
        self.generate.setEnabled(False)
        self.status.setText("Generating translations locally…")
        self.progress.setValue(0)
        self.worker = TranslationWorker(code, model, parent=self)
        self.worker.progress.connect(lambda done, total, _: self.progress.setValue(int(done * 100 / max(total, 1))))
        self.worker.completed.connect(self._completed)
        self.worker.failed.connect(self._failed)
        self.worker.start()

    def _completed(self, language: str, count: int) -> None:
        self.progress.setValue(100)
        self.status.setText(f"Updated {count} translation entries for {dict(LANGUAGES)[language]}.")
        self.generate.setEnabled(True)
        self.manager.reload_catalogs()

    def _failed(self, message: str) -> None:
        self.status.setText(f"Translation generation failed: {message}")
        self.generate.setEnabled(True)

    def closeEvent(self, event) -> None:
        if self.worker and self.worker.isRunning():
            self.worker.requestInterruption()
            self.worker.wait(1000)
        super().closeEvent(event)
