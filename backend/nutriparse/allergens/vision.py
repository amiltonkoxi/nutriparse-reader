"""Visual readers for table cells on scanned pages.

General OCR reads paragraphs well but drops what matters most in allergen
tables: a lone "N" in a cell, or which tick box is filled. Both readers
below use the word boxes found by OCR to look at a small, known region of
the page image instead of the whole page.

* ``tick_boxes``: for a row like "mentes ☐ tartalmaz ☒ előfordulhat ☐",
  measure the ink inside the box right of each label. The ticked box has
  clearly more ink than the empty ones in the same row (a relative test, so
  it survives different scan contrast).
* ``flag_cells``: for Y/N or I/N tables, re-run OCR on just the flag cell of
  each row with a single-line page segmentation mode.
"""

from __future__ import annotations

import re
from collections import Counter

from ..document import Line, Page
from ..text import clip, norm
from .lexicon import find_mentions
from .rules import ABSENT, CONTAINS, Evidence, find_labels

_FLAG_TOKENS = {"I": CONTAINS, "Y": CONTAINS, "IGEN": CONTAINS, "YES": CONTAINS,
                "N": ABSENT, "NEM": ABSENT, "NO": ABSENT}
_TAIL_FLAGS = {"I": "yes", "Y": "yes", "IGEN": "yes", "YES": "yes", "TAK": "yes",
               "N": "no", "NEM": "no", "NO": "no", "NIE": "no", "X": "x"}
_FLAG_HEADER = re.compile(r"\((?:i|y|u|l|1)\s*/\s*n\)|^i\s*/\s*n$|^y\s*/\s*n$")

MIN_INK = 0.08
RATIO = 1.35


def _ink(page: Page, box: tuple[float, float, float, float]) -> float:
    """Share of dark pixels inside a tick box.

    If the crop contains the box outline, only the inside of the outline is
    measured: an empty box then scores near 0 and a ticked one clearly
    higher, whatever the line width or the scan resolution.
    """
    k = page.image_scale
    x0, y0, x1, y1 = (int(round(v * k)) for v in box)
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(page.image.width, x1), min(page.image.height, y1)
    if x1 - x0 < 3 or y1 - y0 < 3:
        return 0.0
    crop = page.image.crop((x0, y0, x1, y1))
    w, h = crop.size
    px = crop.load()
    # Adaptive threshold: blurred scans draw box lines in grey, not black.
    values = sorted(crop.getdata())
    p5, med = values[len(values) // 20], values[len(values) // 2]
    thr = (p5 + med) / 2 if med - p5 > 40 else 128
    dark = [[px[i, j] < thr for i in range(w)] for j in range(h)]
    cols = [i for i in range(w) if sum(dark[j][i] for j in range(h)) > 0.45 * h]
    rows = [j for j in range(h) if sum(dark[j]) > 0.45 * w]
    if len(cols) >= 2 and len(rows) >= 2 and cols[-1] - cols[0] > 3 and rows[-1] - rows[0] > 3:
        a, b = cols[0], cols[-1]
        c, d = rows[0], rows[-1]
        mx, my = max(1, (b - a) // 6), max(1, (d - c) // 6)
        cells = [dark[j][i] for j in range(c + my, d - my + 1) for i in range(a + mx, b - mx + 1)]
        if cells:
            return sum(cells) / len(cells)
    return sum(sum(r) for r in dark) / (w * h)


def _row_category(line: Line) -> str | None:
    cats = {m.allergen for m in find_mentions(norm(line.text))}
    return next(iter(cats)) if len(cats) == 1 else None


def _labels(line: Line):
    """(last word of the label, status) for each status label in a row."""
    tokens = [norm(w.text).strip(".,:;()[]@_") for w in line.words]
    return [(line.words[j], st) for _, j, st in find_labels(tokens)]


def tick_box_rows(page: Page) -> bool:
    """Does the page have rows with two or more status labels?"""
    for ln in page.lines:
        if len({st for _, st in _labels(ln)}) >= 2 and _row_category(ln):
            return True
    return False


def tick_boxes(page: Page) -> list[Evidence]:
    if page.image is None:
        return []
    out: list[Evidence] = []
    for ln in page.lines:
        cat = _row_category(ln)
        if cat is None:
            continue
        labels = _labels(ln)
        if len({st for _, st in labels}) < 2:
            continue
        heights = sorted(w.bottom - w.top for w, _ in labels)
        hm = heights[len(heights) // 2]
        centres = sorted(w.yc for w, _ in labels)
        yc = centres[len(centres) // 2]
        scores = []
        for w, st in labels:
            # the box sits just right of its label, on the row's centre line
            box = (w.x1 + 0.15 * hm, yc - 0.8 * hm, w.x1 + 1.6 * hm, yc + 0.8 * hm)
            scores.append((_ink(page, box), st))
        scores.sort(reverse=True)
        best, second = scores[0], scores[1]
        clear = best[0] >= MIN_INK and best[0] >= RATIO * max(second[0], 1e-6)
        faint = best[0] >= MIN_INK / 2 and best[0] >= 1.8 * max(second[0], 1e-6)
        if clear or faint:
            out.append(Evidence(cat, best[1], "checkbox", clip(ln.text, 0, len(ln.text), pad=0), page.number))
    return out


def flag_cells(page: Page, skip: set[str]) -> list[Evidence]:
    """OCR the flag cell of each row under a "(Y/N)" or "(I/N)" header."""
    if page.image is None:
        return []
    header = None
    for ln in page.lines:
        for w in ln.words:
            if _FLAG_HEADER.search(norm(w.text)) and w.x0 > 0.5 * page.width:
                header = w
        if header:
            break
    if header is None:
        return []
    import pytesseract

    rows: list[tuple[Line, str]] = []
    for ln in page.lines:
        if ln.top <= header.bottom:
            continue
        c = _row_category(ln)
        if not c:
            continue
        if rows and rows[-1][1] == c:
            continue  # same row wrapped over several lines: keep its first line
        rows.append((ln, c))
    out: list[Evidence] = []
    half = max(header.x1 - header.x0, 0.05 * page.width)
    for k, (ln, cat) in enumerate(rows):
        if cat in skip:
            continue
        h = ln.bottom - ln.top
        y0 = ln.top - 0.4 * h
        y1 = rows[k + 1][0].top - 0.2 * h if k + 1 < len(rows) else ln.bottom + 2.5 * h
        if y1 <= y0 + 0.8 * h:
            y1 = ln.bottom + 0.4 * h
        x0, x1 = header.xc - half, header.xc + half
        crop = page.image.crop((int(max(0, x0)), int(max(0, y0)),
                                int(min(page.image.width, x1)), int(min(page.image.height, y1))))
        txt = pytesseract.image_to_string(
            crop, config="--psm 6 -c tessedit_char_whitelist=INYXinyxGEMOgemo"
        )
        toks = [t.upper() for t in re.findall(r"[A-Za-z]+", txt)]
        flags = {_FLAG_TOKENS[t] for t in toks if t in _FLAG_TOKENS}
        if len(flags) == 1:
            out.append(Evidence(cat, flags.pop(), "table_flags", ln.text[:120], page.number))
    return out


def row_tails(page: Page, skip: set[str], x_means_traces: bool) -> list[Evidence]:
    """Re-read the right-hand end of each allergen row on a scanned page.

    Used for I/N, Y/N and two-column tables without a recognised header:
    general OCR tends to drop or garble lone letters in table cells, while a
    single-line OCR of just that strip reads them reliably.
    """
    if page.image is None:
        return []
    import pytesseract

    from .rules import _interpret

    reads: list[tuple[Line, str, list[str]]] = []
    for ln in page.lines:
        cat = _row_category(ln)
        if cat is None or cat in skip:
            continue
        label_words = [w for w in ln.words if len(norm(w.text).strip(".,:;()[]|")) > 2]
        if not label_words:
            continue
        x0 = max(w.x1 for w in label_words) + 0.5 * (ln.bottom - ln.top)
        if x0 > 0.9 * page.width:
            continue
        h = ln.bottom - ln.top
        k = page.image_scale
        box = (int(x0 * k), int(max(0, (ln.top - 0.35 * h) * k)),
               int(page.width * 0.98 * k), int((ln.bottom + 0.35 * h) * k))
        if box[2] - box[0] < 10:
            continue
        txt = pytesseract.image_to_string(
            page.image.crop(box), config="--psm 7 -c tessedit_char_whitelist=INXYTAKGEMOSigenmotakyxs"
        )
        toks = [t.upper() for t in re.findall(r"[A-Za-z]+", txt)]
        if toks and len(toks) <= 3 and all(t in _TAIL_FLAGS for t in toks):
            reads.append((ln, cat, toks))
    if not reads:
        return []
    if not x_means_traces and any("X" in t for _, _, t in reads):
        # X marks without an "(X) = cross contamination" legend: this is an
        # X-mark table whose columns we could not locate. Do not guess.
        return []
    # A table has a fixed number of flag columns. A row where OCR found fewer
    # flags than the table has columns is dropped: reading "N" from "N I"
    # would turn traces into absent.
    counts = Counter(len(t) for _, _, t in reads)
    columns = max(len(t) for _, _, t in reads)
    if counts[columns] < 3:
        return []
    out: list[Evidence] = []
    done: set[str] = set()
    for ln, cat, toks in reads:
        if len(toks) != columns or cat in done:
            continue
        status = _interpret([_TAIL_FLAGS[t] for t in toks], x_means_traces)
        if status:
            out.append(Evidence(cat, status, "table_flags", ln.text[:120], page.number))
            done.add(cat)
    return out
