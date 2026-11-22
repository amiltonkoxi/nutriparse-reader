"""Layout-aware document model.

Both extraction paths (the PDF text layer and OCR) produce the same thing:
pages made of words with bounding boxes. Rules can then use plain text
(lines) or geometry (columns of a table) without caring where the words
came from.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Word:
    text: str
    x0: float
    top: float
    x1: float
    bottom: float

    @property
    def xc(self) -> float:
        return (self.x0 + self.x1) / 2

    @property
    def yc(self) -> float:
        return (self.top + self.bottom) / 2


@dataclass
class Line:
    words: list[Word]
    page: int  # 1-based

    @property
    def text(self) -> str:
        return " ".join(w.text for w in self.words)

    @property
    def top(self) -> float:
        return min(w.top for w in self.words)

    @property
    def bottom(self) -> float:
        return max(w.bottom for w in self.words)

    @property
    def yc(self) -> float:
        return (self.top + self.bottom) / 2


@dataclass
class Page:
    number: int  # 1-based
    width: float
    height: float
    source: str  # "text" | "ocr"
    words: list[Word] = field(default_factory=list)
    lines: list[Line] = field(default_factory=list)
    image: Any = None  # grayscale PIL image, used by the visual cell readers
    image_scale: float = 1.0  # image pixels per word-coordinate unit


@dataclass
class Document:
    pages: list[Page]
    source_path: str | None = None

    @property
    def page_count(self) -> int:
        return len(self.pages)

    @property
    def ocr_pages(self) -> list[int]:
        return [p.number for p in self.pages if p.source == "ocr"]

    @property
    def mode(self) -> str:
        sources = {p.source for p in self.pages}
        if sources == {"ocr"}:
            return "ocr"
        if "ocr" in sources:
            return "mixed"
        return "text"

    def lines(self) -> list[Line]:
        return [ln for p in self.pages for ln in p.lines]

    def text(self) -> str:
        return "\n".join(ln.text for ln in self.lines())


def group_lines(words: list[Word], page: int, tol: float = 0.5) -> list[Line]:
    """Group words into reading-order lines.

    Two words share a line when their vertical centres differ by less than
    ``tol`` times the median word height.
    """
    if not words:
        return []
    heights = sorted(max(1e-3, w.bottom - w.top) for w in words)
    h = heights[len(heights) // 2]
    ordered = sorted(words, key=lambda w: (w.yc, w.x0))
    lines: list[list[Word]] = []
    for w in ordered:
        if lines and abs(w.yc - _yc(lines[-1])) <= tol * h:
            lines[-1].append(w)
        else:
            lines.append([w])
    return [Line(sorted(ws, key=lambda w: w.x0), page) for ws in lines]


def _yc(ws: list[Word]) -> float:
    return sum(w.yc for w in ws) / len(ws)
