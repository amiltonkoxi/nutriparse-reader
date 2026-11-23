"""Text normalisation shared by every rule.

All matching happens on a *normalised* copy of the text: accents removed and
lower case. The normalisation is strictly character-for-character, so an
offset found in the normalised text is the same offset in the original text.
That is what lets every result point back to the exact words in the document.
"""

from __future__ import annotations

import re
from functools import lru_cache

from unidecode import unidecode

# Ticked and empty check boxes keep a visible marker after normalisation.
CHECKED = "@"
UNCHECKED = "_"
_CHECKED_GLYPHS = set("☒☑✓✔■✗✘⊠")
_UNCHECKED_GLYPHS = set("☐□")


@lru_cache(maxsize=4096)
def _norm_char(c: str) -> str:
    if c in _CHECKED_GLYPHS:
        return CHECKED
    if c in _UNCHECKED_GLYPHS:
        return UNCHECKED
    if c in "\t \r":
        return " "
    if c == "\n":
        return "\n"
    u = unidecode(c)
    if not u:
        return " "
    return u[0].lower()


def norm(text: str) -> str:
    """Lower-case ASCII form of ``text`` with ``len(norm(t)) == len(t)``."""
    if not text:
        return ""
    return "".join(_norm_char(c) for c in text)


_WS = re.compile(r"\s+")


def clip(text: str, start: int, end: int, pad: int = 32) -> str:
    """Readable one-line snippet around ``text[start:end]``."""
    a = max(0, start - pad)
    b = min(len(text), end + pad)
    snippet = _WS.sub(" ", text[a:b]).strip()
    if a > 0:
        snippet = "…" + snippet
    if b < len(text):
        snippet += "…"
    return snippet


def squash(text: str) -> str:
    return _WS.sub(" ", text).strip()


def for_nutrition(raw: str) -> str:
    """Normalisation expected by the nutrition parser (v0.3 contract)."""
    if not raw:
        return ""
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", raw)
    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    text = re.sub(r"(\d),(\d)", r"\1.\2", text)
    return unidecode(text).lower().strip()
