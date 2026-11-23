"""Build in-memory documents for tests without any PDF."""

from __future__ import annotations

from nutriparse.document import Document, Line, Page, Word

CHAR_W = 5.0
LINE_H = 10.0


def make_page(lines: list[str], number: int = 1, width: float = 600.0,
              positions: dict[int, list[tuple[str, float]]] | None = None) -> Page:
    """One page; each string is a line. ``positions`` can pin words of a line
    to x coordinates: {line_index: [(word, x0), ...]}."""
    page = Page(number, width, 800.0, "text")
    for i, text in enumerate(lines):
        top = 20 + i * (LINE_H + 4)
        words: list[Word] = []
        if positions and i in positions:
            for w, x0 in positions[i]:
                words.append(Word(w, x0, top, x0 + CHAR_W * len(w), top + LINE_H))
        else:
            x = 20.0
            for w in text.split():
                words.append(Word(w, x, top, x + CHAR_W * len(w), top + LINE_H))
                x += CHAR_W * (len(w) + 1)
        if words:
            page.words += words
            page.lines.append(Line(words, number))
    return page


def make_doc(lines: list[str], **kw) -> Document:
    return Document([make_page(lines, **kw)])
