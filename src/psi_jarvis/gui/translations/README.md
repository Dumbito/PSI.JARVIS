# GUI translation catalogs

The English source strings live in the Python GUI. `scripts/generate_i18n.py` extracts user-visible literals, including long-form explanatory text, tutorial content, dialogs, tooltips and status messages, then fills `ui_<language>.json` through a local Ollama model.

Supported targets: Spanish, French, German, Italian, Portuguese, Japanese, Chinese and Korean.

The runtime `LanguageManager` treats these catalogs as presentation-only data. Scientific decisions, provenance and persisted screening evidence are never translated or modified.
