"""Evidence rules.

Each rule looks for one way that real specification sheets declare
allergens and returns ``Evidence`` items. No rule ever invents an
"absent": absence needs a statement, a table cell or a tick in the
document. Deciding the final status is the job of ``fusion.py``.

Formats covered (all observed in real Hungarian/Polish supplier sheets):

=====================  ===================================================
rule                   example
=====================  ===================================================
ingredients            "Összetevők: búzaliszt, tyúktojás, ivóvíz"
statement              "Nyomokban tejet, zellert, szóját tartalmazhat."
global_statement       "ALLERGÉN ANYAGOKAT NEM TARTALMAZ." / "No allergens"
table_flags            "Tej és származékai   I   N"  (I/N, Igen/Nem, Y/N)
checkbox               "Tej ...  mentes ☐  tartalmaz ☒  előfordulhat ☐"
grid                   "01 + milk protein   15 - Cocoa"
layout_table           X marks placed under Igen / Nem / Kereszt columns
implicit_declaration   "Allergén információ: hal."  (others not listed)
=====================  ===================================================
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from ..document import Document, Line
from ..text import CHECKED, UNCHECKED, clip, norm
from .lexicon import ALLERGENS, Mention, find_mentions

CONTAINS, TRACES, ABSENT = "contains", "traces", "absent"


@dataclass(frozen=True)
class Evidence:
    allergen: str
    status: str
    rule: str
    snippet: str
    page: int | None = None


# --------------------------------------------------------------------------
# Flat text with offsets back to lines and pages
# --------------------------------------------------------------------------


@dataclass
class Context:
    doc: Document
    lines: list[Line]
    text: str  # original
    ntext: str  # normalised, same length
    line_starts: list[int] = field(default_factory=list)

    @classmethod
    def build(cls, doc: Document) -> Context:
        lines = doc.lines()
        parts: list[str] = []
        starts: list[int] = []
        pos = 0
        prev: Line | None = None
        for ln in lines:
            sep = ""
            if prev is not None:
                sep = "\n"
                gap = ln.top - prev.bottom
                height = max(1.0, prev.bottom - prev.top)
                if ln.page != prev.page or gap > 1.2 * height:
                    sep = "\n\n"  # paragraph break
            parts.append(sep)
            pos += len(sep)
            starts.append(pos)
            t = ln.text
            parts.append(t)
            pos += len(t)
            prev = ln
        text = "".join(parts)
        return cls(doc, lines, text, norm(text), starts)

    def line_index(self, offset: int) -> int:
        lo, hi = 0, len(self.line_starts) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if self.line_starts[mid] <= offset:
                lo = mid
            else:
                hi = mid - 1
        return lo

    def page_of(self, offset: int) -> int | None:
        if not self.lines:
            return None
        return self.lines[self.line_index(offset)].page

    def line_span(self, i: int) -> tuple[int, int]:
        s = self.line_starts[i]
        return s, s + len(self.lines[i].text)


# --------------------------------------------------------------------------
# Shared vocabulary (normalised text)
# --------------------------------------------------------------------------

_TRACES = (
    r"nyomokban|tartalmazhat|elofordulhat|kereszt[- ]?szennyez\w*|may\s+contain|traces?\s+of|"
    r"cross[- ]?contam\w*|moze\s+zawierac|moga\s+zawierac|sladow\w*"
)
_ABSENT = (
    r"mentes(?![a-z])|mentesek|nem\s+tartalmaz\w*|free\s+(?:from|of)|-free(?![a-z])|"
    r"does\s+not\s+contain|do\s+not\s+contain|nie\s+zawiera\w*"
)
_CONTAINS = r"tartalmaz(?:za|zak|nak)?(?![a-z])|contains?(?![a-z])|zawiera(?:ja)?(?![a-z])"

RX_TRACES = re.compile(_TRACES)
RX_ABSENT = re.compile(_ABSENT)
RX_CONTAINS = re.compile(_CONTAINS)

# "Allergen information:" style header followed by a list.
RX_DECL_HEADER = re.compile(
    r"allerg\w*\s*(?:informaci\w*|information|info|osszetev\w*|components?|deklaraci\w*|"
    r"anyag\w*\s+tartalmaz\w*)?\s*:"
    r"|alergen\w*\s*:"
)

# A whole document saying it has no allergens at all.
RX_GLOBAL_ABSENT = re.compile(
    r"allerg[eé]n\w*\s+(?:anyag\w*\s+)?nem\s+tartalmaz|"
    r"(?<![a-z])no\s+allergens?(?![a-z])|allergen[- ]?free|allergen\s?mentes(?!seg)|"
    r"brak\s+alergen|nie\s+zawiera\w*\s+alergen|free\s+(?:from|of)\s+(?:all\s+)?allergens|"
    r"allerg\w*\s*:\s*(?:nincs|none|nincsenek)(?![a-z])|does\s+not\s+contain\s+(?:any\s+)?allergens"
)

# Phrases used in the rows of Annex II tables ("X and products thereof").
RX_ROW_PHRASE = re.compile(
    r"(?:abbol|belole|beloluk|azokbol|ezekbol|bol)\s+keszult|szarmazek|products?\s+(?:made|thereof|based)|"
    r"and\s+products|i\s+produkty|pochodne"
)

RX_SECTION_START = re.compile(r"^\s*(?:[0-9]{1,2}|[ivx]{1,4})[./)]+\s*")

_FLAG_WORD = {
    "I": "yes", "Y": "yes", "Igen": "yes", "IGEN": "yes", "igen": "yes", "Yes": "yes", "YES": "yes",
    "yes": "yes", "Tak": "yes", "TAK": "yes", "tak": "yes", "+": "yes",
    "N": "no", "Nem": "no", "NEM": "no", "nem": "no", "No": "no", "NO": "no", "no": "no",
    "Nie": "no", "NIE": "no", "nie": "no",
    "X": "x",
    "-": "dash", "–": "dash", "—": "dash",
}
_UPPER_FLAGS = {"I", "N", "X", "Y"}
_NUMBER = re.compile(r"^[\d.,%/()\[\]]+$")


# --------------------------------------------------------------------------
# Rules
# --------------------------------------------------------------------------


def rule_ingredients(ctx: Context) -> list[Evidence]:
    """Allergens named in the ingredient list are contained in the product."""
    out: list[Evidence] = []
    rx = re.compile(
        r"^\s*(?:(?:[0-9]{1,2}|[ivx]{1,4})[./)]+\s*/?\s*)*"
        r"(?:osszetevok?(?:\s+felsorolasa)?|osszetetel|ingredients?|skladniki|sklad)(?![a-z])"
        r"(?:\s*/\s*(?:ingredients?|skladniki))?\s*(?:[:/]|$)"
    )
    # An ingredient list ends where a sentence about allergens starts.
    stop = re.compile(r"\.\s+(?=[a-z])|" + _TRACES + r"|allerg|alergen")
    n = len(ctx.lines)
    i = 0
    while i < n:
        s, e = ctx.line_span(i)
        m = rx.match(ctx.ntext[s:e])
        if not m:
            i += 1
            continue
        start = s + m.end()
        end = e
        j = i + 1
        while j < n and j <= i + 5:
            js, je = ctx.line_span(j)
            nl = ctx.ntext[js:je]
            if ctx.ntext[ctx.line_starts[j] - 2 : ctx.line_starts[j]] == "\n\n" and end > start + 3:
                break
            if RX_SECTION_START.match(nl) or re.match(r"^\s*[a-z][a-z /]{2,40}:", nl):
                break
            end = je
            j += 1
        cut = stop.search(ctx.ntext, start, end)
        if cut and _is_sentence_break(ctx.text, cut.start()):
            end = cut.start()
        elif cut and not ctx.ntext[cut.start()] == ".":
            end = cut.start()
        for mt in find_mentions(ctx.ntext, start, end):
            out.append(Evidence(mt.allergen, CONTAINS, "ingredients",
                                clip(ctx.text, mt.start, mt.end), ctx.page_of(mt.start)))
        i = j
    return out


def _is_sentence_break(text: str, i: int) -> bool:
    """A full stop followed by a capital letter."""
    if text[i] != ".":
        return False
    j = i + 1
    while j < len(text) and text[j].isspace():
        j += 1
    return j < len(text) and text[j].isupper()


def _sentences(ctx: Context) -> list[tuple[int, int]]:
    """Sentence spans: split on . ; ! ? (not inside numbers), on paragraph
    breaks and before numbered section headings."""
    t = ctx.ntext
    spans: list[tuple[int, int]] = []
    start = 0
    i = 0
    L = len(t)
    while i < L:
        c = t[i]
        cut = False
        if c in ";!?":
            cut = True
        elif c == ".":
            prev_digit = i > 0 and t[i - 1].isdigit()
            next_digit = i + 1 < L and t[i + 1].isdigit()
            cut = not (prev_digit and next_digit)
        elif c == "\n":
            if i + 1 < L and t[i + 1] == "\n":
                cut = True
            elif RX_SECTION_START.match(t[i + 1 : i + 8]):
                cut = True
        if cut:
            if i > start:
                spans.append((start, i))
            start = i + 1
        i += 1
    if start < L:
        spans.append((start, L))
    return spans


_CONNECTORS = {"es", "and", "i", "oraz", "valamint", "illetve", "or", "vagy", "lub", "a", "az"}


def _gap_words(ntext: str, a: int, b: int, mentions: list[Mention]) -> int:
    """Non-allergen, non-connector words between offsets a < b."""
    if b <= a:
        return 0
    covered = [(m.start, m.end) for m in mentions if a <= m.start < b]
    count = 0
    for w in re.finditer(r"[a-z0-9]+", ntext[a:b]):
        ws, we = a + w.start(), a + w.end()
        if any(cs <= ws < ce or ws <= cs < we for cs, ce in covered):
            continue
        if w.group() in _CONNECTORS:
            continue
        count += 1
    return count


def rule_statements(ctx: Context, table_lines: set[int] | None = None) -> tuple[list[Evidence], list[Evidence]]:
    """Free-text statements. Returns (evidence, declarations).

    ``declarations`` are the 'contains' items that came from an explicit
    allergen declaration ("Allergén információ: hal."). They let fusion mark
    the other allergens as implicitly absent.
    """
    out: list[Evidence] = []
    decl: list[Evidence] = []
    t, nt = ctx.text, ctx.ntext
    for s, e in _sentences(ctx):
        sent = nt[s:e]
        if CHECKED in sent or UNCHECKED in sent:
            continue  # tick-box rows are handled by rule_checkbox
        mentions = find_mentions(nt, s, e)
        if table_lines:
            # mentions inside table or grid rows belong to the table rules
            mentions = [m for m in mentions if ctx.line_index(m.start) not in table_lines]
        if not mentions:
            continue
        triggers: list[tuple[int, int, str]] = []
        for rx, status in ((RX_TRACES, TRACES), (RX_ABSENT, ABSENT), (RX_CONTAINS, CONTAINS)):
            for m in rx.finditer(sent):
                triggers.append((s + m.start(), s + m.end(), status))
        header = RX_DECL_HEADER.search(sent)
        if header:
            triggers.append((s + header.start(), s + header.end(), CONTAINS))
        if not triggers:
            continue
        # Remove overlaps: 'tartalmazhat' also matches the 'contains' verb.
        triggers.sort(key=lambda x: (x[0], -(x[1] - x[0])))
        clean: list[tuple[int, int, str]] = []
        for tr in triggers:
            if clean and tr[0] < clean[-1][1]:
                continue
            clean.append(tr)
        statuses = {st for _, _, st in clean}
        allergen_context = "allerg" in sent or "alergen" in sent
        rows = len(RX_ROW_PHRASE.findall(sent))
        if rows >= 2 or (rows >= 1 and len(statuses) >= 2):
            continue  # flattened table, not a sentence
        if allergen_context and len(sent) > 260:
            continue
        max_gap = 12 if allergen_context else 2
        for mt in mentions:
            best = None
            for ts, te, st in clean:
                gap = _gap_words(nt, mt.end, ts, mentions) if ts >= mt.end else _gap_words(nt, te, mt.start, mentions)
                # a colon header only governs what follows it
                if header and ts == s + header.start() and mt.start < te:
                    continue
                if gap <= max_gap and (best is None or gap < best[0]):
                    best = (gap, st, ts)
            if best is None:
                continue
            ev = Evidence(mt.allergen, best[1], "statement", clip(t, mt.start, mt.end), ctx.page_of(mt.start))
            out.append(ev)
            if best[1] == CONTAINS and allergen_context:
                decl.append(ev)
    return out, decl


def rule_global(ctx: Context) -> list[Evidence]:
    out: list[Evidence] = []
    for m in RX_GLOBAL_ABSENT.finditer(ctx.ntext):
        snippet = clip(ctx.text, m.start(), m.end())
        page = ctx.page_of(m.start())
        out.extend(Evidence(a, ABSENT, "global_statement", snippet, page) for a in ALLERGENS)
        break
    return out


def _line_flags(line: Line, after_char: int) -> list[str]:
    """Status flags in a table row, left to right."""
    flags: list[tuple[int, str]] = []
    pos = 0
    words = line.words
    offsets = []
    for w in words:
        offsets.append(pos)
        pos += len(w.text) + 1
    # trailing run of flag/number tokens
    trailing_start = len(words)
    for k in range(len(words) - 1, -1, -1):
        tok = words[k].text.strip(".,;:")
        if tok in _FLAG_WORD or _NUMBER.match(tok):
            trailing_start = k
        else:
            break
    for k, w in enumerate(words):
        if offsets[k] < after_char:
            continue
        tok = w.text.strip(".,;:")
        if tok in _UPPER_FLAGS or (k >= trailing_start and tok in _FLAG_WORD):
            flags.append((k, _FLAG_WORD[tok]))
    return [f for _, f in flags]


def _interpret(flags: list[str], x_means_traces: bool) -> str | None:
    if not flags:
        return None
    if len(flags) == 1:
        f = flags[0]
        if f == "yes":
            return CONTAINS
        if f == "no":
            return ABSENT
        if f == "x" and x_means_traces:
            return TRACES
        return None
    a, b = flags[0], flags[1]
    if a == "yes":
        return CONTAINS
    if b in ("yes", "x"):
        return TRACES
    if a == "no" and b in ("no", "dash"):
        return ABSENT
    if a == "x" and x_means_traces:
        return TRACES
    return None


RX_X_LEGEND = re.compile(r"\(x\)|i\s*/\s*n\s*/\s*x|x\s*[=:]\s*(?:kereszt|cross|traces|nyom)")


def _single_category(nl: str) -> tuple[str | None, list[Mention]]:
    ms = find_mentions(nl)
    cats = {m.allergen for m in ms}
    if len(cats) == 1:
        return next(iter(cats)), ms
    return None, ms


def rule_table_flags(ctx: Context, skip_lines: set[int]) -> tuple[list[Evidence], set[int]]:
    """Rows of Annex II tables ending in I/N, Igen/Nem, Y/N or two columns."""
    out: list[Evidence] = []
    rows_done: set[int] = set()
    n = len(ctx.lines)
    for i, ln in enumerate(ctx.lines):
        if i in skip_lines:
            continue
        s, e = ctx.line_span(i)
        nl = ctx.ntext[s:e]
        if CHECKED in nl or UNCHECKED in nl:
            continue
        cat, ms = _single_category(nl)
        if cat is None:
            continue
        flags = _line_flags(ln, ms[0].start)
        if not flags and i + 1 < n:
            nxt = ctx.lines[i + 1]
            ns, ne = ctx.line_span(i + 1)
            toks = [w.text.strip(".,;:") for w in nxt.words]
            if (not find_mentions(ctx.ntext, ns, ne) and toks
                    and all(tk in _FLAG_WORD or _NUMBER.match(tk) for tk in toks)
                    and any(tk in _FLAG_WORD and tk != "-" for tk in toks)):
                flags = [_FLAG_WORD[tk] for tk in toks if tk in _FLAG_WORD]
        if not flags:
            continue
        lo = ctx.line_starts[max(0, i - 30)]
        x_legend = bool(RX_X_LEGEND.search(ctx.ntext[lo:e]))
        status = _interpret(flags, x_legend)
        if status is None:
            continue
        rows_done.add(i)
        out.append(Evidence(cat, status, "table_flags", clip(ctx.text, s, e, pad=0), ln.page))
    return out, rows_done


# Status labels next to tick boxes. Longer phrases first.
_LABEL_PHRASES: list[tuple[tuple[str, ...], str]] = [
    (("does", "not", "contain"), ABSENT), (("nie", "zawiera"), ABSENT), (("nem", "tartalmaz"), ABSENT),
    (("moze", "zawierac"), TRACES), (("may", "contain"), TRACES),
    (("mentes",), ABSENT), (("free",), ABSENT), (("absent",), ABSENT), (("nem",), ABSENT),
    (("no",), ABSENT), (("nie",), ABSENT),
    (("elofordulhat",), TRACES), (("tartalmazhat",), TRACES), (("nyomokban",), TRACES), (("traces",), TRACES),
    (("tartalmaz",), CONTAINS), (("contains",), CONTAINS), (("zawiera",), CONTAINS), (("igen",), CONTAINS),
    (("yes",), CONTAINS), (("tak",), CONTAINS),
]


def find_labels(tokens: list[str]) -> list[tuple[int, int, str]]:
    """Status label phrases in a token list: (first index, last index, status)."""
    out: list[tuple[int, int, str]] = []
    i = 0
    while i < len(tokens):
        for phrase, status in _LABEL_PHRASES:
            k = len(phrase)
            if tuple(tokens[i : i + k]) == phrase:
                out.append((i, i + k - 1, status))
                i += k
                break
        else:
            i += 1
    return out


def _box_next_to(seq: list[str], pos: list[int], label: tuple[int, int, str], after: bool) -> str | None:
    """The tick-box marker right after (or before) a label, if any."""
    k = pos[label[1]] + 1 if after else pos[label[0]] - 1
    if 0 <= k < len(seq) and seq[k] in (CHECKED, UNCHECKED):
        return seq[k]
    return None


def rule_checkbox(ctx: Context) -> list[Evidence]:
    """Rows with tick-box glyphs: "mentes ☐  tartalmaz ☒  előfordulhat ☐"."""
    out: list[Evidence] = []
    for i, ln in enumerate(ctx.lines):
        s, e = ctx.line_span(i)
        nl = ctx.ntext[s:e]
        if CHECKED not in nl:
            continue
        cat, _ = _single_category(nl)
        if cat is None:
            continue
        # Sequence of tokens and box markers, e.g. ["mentes", @, "tartalmaz", _]
        seq: list[str] = []
        for w in ln.words:
            t = norm(w.text)
            lead = len(t) - len(t.lstrip(CHECKED + UNCHECKED))
            seq += [c for c in t[:lead]]
            base = t.strip(CHECKED + UNCHECKED).strip(".,:;()[]")
            if base:
                seq.append(base)
            trail = t[len(t.rstrip(CHECKED + UNCHECKED)):] if t.strip(CHECKED + UNCHECKED) else ""
            seq += [c for c in trail]
        tokens = [x for x in seq if x not in (CHECKED, UNCHECKED)]
        # map token index -> position in seq
        pos = [k for k, x in enumerate(seq) if x not in (CHECKED, UNCHECKED)]
        labels = find_labels(tokens)
        if len({st for _, _, st in labels}) < 2:
            continue

        after = sum(_box_next_to(seq, pos, lb, True) is not None for lb in labels)
        before = sum(_box_next_to(seq, pos, lb, False) is not None for lb in labels)
        use_after = after >= before
        ticked = {lb[2] for lb in labels if _box_next_to(seq, pos, lb, use_after) == CHECKED}
        if len(ticked) == 1:
            out.append(Evidence(cat, ticked.pop(), "checkbox", clip(ctx.text, s, e, pad=0), ln.page))
    return out


RX_GRID_ENTRY = re.compile(r"(?:(?<=\s)|^)(\d{1,2})\s+([+\-])\s+(?=[a-z])")


def rule_grid(ctx: Context) -> tuple[list[Evidence], set[int]]:
    """Numbered +/- grids: "01 + milk protein/ tejfehérje   15 - Cocoa"."""
    entries: list[tuple[int, str, int, int]] = []  # line, sign, start, end
    grid_lines: set[int] = set()
    last_line = -10
    for i, _ln in enumerate(ctx.lines):
        s, e = ctx.line_span(i)
        nl = ctx.ntext[s:e]
        found = list(RX_GRID_ENTRY.finditer(nl))
        if found:
            grid_lines.add(i)
            for k, m in enumerate(found):
                a = s + m.end()
                b = s + found[k + 1].start() if k + 1 < len(found) else e
                entries.append((i, m.group(2), a, b))
            last_line = i
        elif entries and i == last_line + 1 and len(nl) < 40 and not RX_SECTION_START.match(nl):
            # wrapped continuation of the previous entry ("crustaceans/kagyló és")
            li, sign, a, b = entries[-1]
            if li == last_line:
                entries.append((i, sign, s, e))
                grid_lines.add(i)
                last_line = i
    if len(entries) < 4:
        return [], set()
    plus_is_either = bool(re.search(
        r"\+\s*[=:]?\s*(?:tartalmaz|contains?|zawiera)\s*/\s*(?:tartalmazhat|may|moze)", ctx.ntext))
    out: list[Evidence] = []
    for i, sign, a, b in entries:
        if sign == "+":
            status = TRACES if plus_is_either else CONTAINS
        else:
            status = ABSENT
        for mt in find_mentions(ctx.ntext, a, b):
            out.append(Evidence(mt.allergen, status, "grid", clip(ctx.text, a, b, pad=0), ctx.lines[i].page))
    return out, grid_lines


_HEAD = {
    CONTAINS: {"igen", "yes", "tak", "tartalmaz", "contains", "jelen", "i", "y"},
    ABSENT: {"nem", "no", "nie", "mentes", "free", "n"},
    TRACES: {"nyomokban", "elofordulhat", "veletlen", "may", "traces"},
}
_HEAD_PREFIX_TRACES = ("kereszt", "cross", "zanieczyszcz", "traces")
_MARKS = {"x", "×", "@", "v"}


def column_headers(page) -> list[tuple[int, list[tuple[float, str]]]]:
    """Lines that look like status column headings (Igen | Nem | Kereszt...)."""
    found = []
    for hi, hl in enumerate(page.lines):
        cols: list[tuple[float, str]] = []
        for w in hl.words:
            if w.x0 < 0.35 * page.width:
                continue
            tok = norm(w.text).strip(".,:;()/")
            for st, heads in _HEAD.items():
                if tok in heads:
                    cols.append((w.xc, st))
            if tok.startswith(_HEAD_PREFIX_TRACES):
                cols.append((w.xc, TRACES))
        if len({st for _, st in cols}) >= 2:
            found.append((hi, cols))
    return found


def rule_layout_table(ctx: Context, rows_done: set[int]) -> list[Evidence]:
    """Tables where the status is an X placed under a column heading.

    Text alone cannot tell which column an X is in, so this rule uses the
    word coordinates: the X goes to the nearest heading horizontally and
    to the nearest allergen row vertically.
    """
    out: list[Evidence] = []
    done_keys = {(ctx.lines[i].page, round(ctx.lines[i].yc)) for i in rows_done}
    for page in ctx.doc.pages:
        lines = page.lines
        for hi, cols in column_headers(page):
            # rows below the header
            row_lines: list[tuple[Line, str]] = []
            marks: list[tuple[float, float]] = []
            misses = 0
            for ln in lines[hi + 1 : hi + 40]:
                nl = norm(ln.text)
                cat, _ = _single_category(nl)
                if cat:
                    row_lines.append((ln, cat))
                    misses = 0
                else:
                    misses += 1
                for w in ln.words:
                    if norm(w.text).strip(".,;:()[]|") in _MARKS and w.x0 > 0.4 * page.width:
                        marks.append((w.xc, w.yc))
                if misses > 4 and row_lines:
                    break
            if len(row_lines) < 3 or not marks:
                continue
            col_gap = min((abs(a[0] - b[0]) for a in cols for b in cols if a is not b), default=page.width)
            heights = sorted(ln.bottom - ln.top for ln, _ in row_lines)
            lh = heights[len(heights) // 2] if heights else 10.0
            assigned: dict[int, set[str]] = {}
            for mx, my in marks:
                col = min(cols, key=lambda c: abs(c[0] - mx))
                if abs(col[0] - mx) > 0.75 * col_gap:
                    continue
                k = min(range(len(row_lines)), key=lambda r: abs(row_lines[r][0].yc - my))
                if abs(row_lines[k][0].yc - my) > 1.6 * lh:
                    continue
                assigned.setdefault(k, set()).add(col[1])
            for k, sts in assigned.items():
                ln, cat = row_lines[k]
                if (ln.page, round(ln.yc)) in done_keys or len(sts) != 1:
                    continue
                out.append(Evidence(cat, sts.pop(), "layout_table", ln.text[:120], ln.page))
            break  # one table header per page is enough
    return out
