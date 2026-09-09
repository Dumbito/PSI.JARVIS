#!/usr/bin/env python3
"""Build complete GUI translation catalogs from all user-visible literals.

The source language is English. Every literal that can become visible in the
Qt GUI is extracted and translated in batches through local Ollama. Existing
translations are preserved and only missing/stale entries are requested.
"""
from __future__ import annotations
import argparse, ast, json, os, re, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "psi_jarvis" / "gui"
OUT = SRC / "translations"
LANGUAGES = {"es":"Spanish","fr":"French","de":"German","it":"Italian","pt":"Portuguese","ja":"Japanese","zh":"Chinese","ko":"Korean"}
SKIP_EXACT = {"", "utf-8", "utf8", "__main__"}
SKIP_RE = re.compile(r"^(?:https?://|/|[A-Z_][A-Z0-9_]+$|[a-z_]+-[a-z0-9_-]+$|[{}()\[\]<>]+$)")


def extract_strings() -> list[str]:
    found: set[str] = set()
    for path in SRC.rglob("*.py"):
        try: tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError): continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                value = " ".join(node.value.split()).strip()
                if _candidate(value): found.add(value)
    return sorted(found, key=str.casefold)


def _candidate(value: str) -> bool:
    if len(value) < 2 or len(value) > 1200 or value in SKIP_EXACT or SKIP_RE.match(value): return False
    if not any(c.isalpha() for c in value): return False
    # Exclude source identifiers and hashes while retaining explanatory prose.
    if "\\" in value and not any(c.isspace() for c in value): return False
    return True


def translate_batch(model: str, language: str, strings: list[str]) -> dict[str,str]:
    base = os.environ.get("PSI_OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
    items = "\n".join(f"{i}: {text}" for i,text in enumerate(strings))
    prompt = f"""You are a professional software localization engine. Translate every item below into {language}.
Return ONLY a JSON object mapping each numeric ID to its translation. Translate labels, buttons, tooltips, dialogs, tutorial/help prose, empty states, status messages and explanatory text naturally.
Preserve placeholders such as {{name}}, format specifiers, numbers, acronyms, technical product names (PSI.JARVIS, Ollama, Qt, JSON, Markdown, CSV, Excel, RIS, PRISMA, ScreeningEngine), emojis, arrows and punctuation. Do not omit, merge, explain or add items.

ITEMS:
{items}"""
    payload = json.dumps({"model":model,"prompt":prompt,"stream":False}).encode()
    req = urllib.request.Request(f"{base}/api/generate", data=payload, headers={"Content-Type":"application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=300) as response: raw = json.loads(response.read().decode()).get("response", "")
    data = json.loads(raw)
    return {source:str(data[str(i)]).strip() for i,source in enumerate(strings) if isinstance(data.get(str(i)), str) and data[str(i)].strip()}


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--model",default="qwen3:8b"); p.add_argument("--batch-size",type=int,default=25); args=p.parse_args()
    OUT.mkdir(parents=True,exist_ok=True); strings=extract_strings(); print(f"Found {len(strings)} user-visible candidates.")
    for code,language in LANGUAGES.items():
        target=OUT/f"ui_{code}.json"; catalog={}
        if target.exists():
            try: catalog={str(k):str(v) for k,v in json.loads(target.read_text(encoding="utf-8")).items()}
            except (OSError,json.JSONDecodeError): catalog={}
        missing=[s for s in strings if s not in catalog]
        print(f"{language}: {len(missing)} missing")
        for start in range(0,len(missing),args.batch_size):
            batch=missing[start:start+args.batch_size]; catalog.update(translate_batch(args.model,language,batch))
            target.write_text(json.dumps(catalog,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
            print(f"  {min(start+len(batch),len(missing))}/{len(missing)}")
    return 0

if __name__ == "__main__": raise SystemExit(main())
