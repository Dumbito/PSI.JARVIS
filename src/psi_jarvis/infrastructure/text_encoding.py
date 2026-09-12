"""Robust text-file reading for bibliographic import formats.

Reference managers (EndNote, older Zotero/Web of Science exports, etc.)
frequently write CSV/RIS files in a legacy Windows codepage rather than
UTF-8, especially when author names or titles contain accented
characters. A hardcoded ``encoding="utf-8"`` read turns any such file
into an unhandled ``UnicodeDecodeError`` for the person importing it.

This tries UTF-8 first (the common, correct case) and only falls back
to legacy encodings when that fails, so well-formed UTF-8 files are
read exactly as before.
"""

from pathlib import Path

_FALLBACK_ENCODINGS = ("utf-8-sig", "cp1252", "latin-1")


def read_text_with_encoding_fallback(path: Path) -> str:
    """Read ``path`` as text, tolerating common legacy encodings.

    Tries UTF-8 first. If that fails, tries a short list of encodings
    commonly produced by older reference-management software. ``latin-1``
    never raises a decode error (every byte value is a valid code
    point), so this always returns *something* rather than crashing -
    the caller's own format parsing (CSV/RIS structure) is still
    responsible for rejecting content that isn't actually valid.
    """
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        pass
    for encoding in _FALLBACK_ENCODINGS:
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    # latin-1 is in _FALLBACK_ENCODINGS and cannot fail to decode, so
    # this line is unreachable in practice; kept as a defensive floor.
    return path.read_text(encoding="latin-1", errors="replace")
