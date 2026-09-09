#!/usr/bin/env python3
"""Generate whole-app UI translation catalogs without editing every widget.

The script extracts user-visible string literals from the Python GUI and asks a
local Ollama model to translate them in batches. Results are cached as JSON
catalogs consumed by LanguageManager at runtime.

Usage:
    python scripts/generate_i18n.py --model qwen3:8b

Environment:
    PSI_OLLAMA_BASE_URL   Ollama endpoint (default: http://127.0.0.1:11434)
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "psi_jarvis" / "gui"
OUT = SRC / "translations"
LANGUAGES = {
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "ja": "Japanese",
    "zh": "Chinese",
    "ko": "Korean",
}

# Strings that are clearly data, identifiers, prompts, or code-like values.
SKIP = re.compile(r"^(?:https?://|/|[A-Z_][A-Z0-9_]+$|[a-z_]+-[a-z0-9_-]+$)")


def extract_strings() -> list[str]:
    found: set[str] = set()
    for path in SRC.rglob("*.py"):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError):
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
                continue
            value = " ".join(node.value.split()).strip()
            if len(value) < 2 or len(value) > 240 or SKIP.match(value):
                continue
            # Keep UI-like phrases and labels, not source-code internals.
            if any(ch.isalpha() for ch in value) and not value.startswith("http"):
                found.add(value)
    return sorted(found, key=str.casefold)


def ollama_translate(model: str, language: str, strings: list[str]) -> dict[str, str]:
    base = os.environ.get("PSI_OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
    numbered = "\n".join(f"{i}: {text}" for i, text in enumerate(strings))
    prompt = f"""You are a professional software UI translator.
Translate every item into {language}.
Return ONLY valid JSON: an object whose keys are the numeric item IDs and whose values are the translations.
Preserve emojis, punctuation, numbers, technical names, acronyms, placeholders, and ellipses.
Do not omit any item and do not add commentary.

ITEMS:
{numbered}
"""
    body = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode("utf-8")
    request = urllib.request.Request(
        f"{base}/api/generate",
        data=body,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        payload = json.loads(response.read().decode("utf-8"))
    raw = str(payload.get("response", "")).strip()
    data = json.loads(raw)
    result: dict[str, str] = {}
    for index, source in enumerate(strings):
        translated = data.get(str(index))
        if isinstance(translated, str) and translated.strip():
            result[source] = translated.strip()
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="qwen3:8b", help="Local Ollama model used for translation")
    parser.add_argument("--batch-size", type=int, default=40)
    args = parser.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    strings = extract_strings()
    print(f"Found {len(strings)} candidate UI strings.")

    for code, language in LANGUAGES.items():
        target = OUT / f"ui_{code}.json"
        catalog: dict[str, str] = {}
        if target.exists():
            try:
                loaded = json.loads(target.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    catalog.update({str(k): str(v) for k, v in loaded.items()})
            except (OSError, json.JSONDecodeError):
                pass

        missing = [text for text in strings if text not in catalog]
        print(f"{language}: {len(missing)} strings missing")
        for start in range(0, len(missing), args.batch_size):
            batch = missing[start : start + args.batch_size]
            catalog.update(ollama_translate(args.model, language, batch))
            target.write_text(
                json.dumps(catalog, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            print(f"  translated {min(start + len(batch), len(missing))}/{len(missing)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
