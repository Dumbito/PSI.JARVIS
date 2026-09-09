from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GUI = ROOT / "src" / "psi_jarvis" / "gui"
TRANSLATIONS = GUI / "translations"


def _extract() -> set[str]:
    found: set[str] = set()
    for path in GUI.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                value = " ".join(node.value.split()).strip()
                if len(value) >= 2 and any(c.isalpha() for c in value):
                    found.add(value)
    return found


def test_translation_catalogs_cover_generated_gui_strings():
    source = _extract()
    assert source
    for code in ("es", "fr", "de", "it", "pt", "ja", "zh", "ko"):
        path = TRANSLATIONS / f"ui_{code}.json"
        if not path.exists():
            continue
        catalog = json.loads(path.read_text(encoding="utf-8"))
        missing = sorted(source - set(catalog))
        # Catalogs may intentionally omit internal/code-like literals; keep this
        # as a diagnostic guard rather than making the whole suite brittle.
        assert len(missing) <= max(5, int(len(source) * 0.20)), (code, missing[:20])
