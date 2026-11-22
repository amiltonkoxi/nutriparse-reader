"""Combine evidence into one status per allergen.

Policy (safety first):

1. ``unknown`` is the default. Nothing becomes ``absent`` without evidence.
2. Direct evidence (ingredients, statements, tables, ticks) beats document-wide
   statements. Among direct evidence the most severe status wins:
   contains > traces > absent. A false "absent" can hurt a consumer; a false
   "contains" only costs a manual check.
3. When direct sources disagree (ingredients say wheat, the table says
   gluten "N") the result keeps the severe status and is flagged as a
   conflict for human review.
4. A global "no allergens" statement, and then an explicit declaration that
   lists other allergens, can only fill gaps. They never override direct
   evidence.
"""

from __future__ import annotations

from dataclasses import dataclass

from .lexicon import ALLERGENS
from .rules import ABSENT, CONTAINS, TRACES, Evidence

SEVERITY = {CONTAINS: 3, TRACES: 2, ABSENT: 1}
RULE_STRENGTH = {
    "table_flags": 5, "checkbox": 5, "layout_table": 5, "grid": 4,
    "statement": 3, "ingredients": 3, "global_statement": 1, "implicit_declaration": 0,
}
DIRECT_RULES = {"table_flags", "checkbox", "layout_table", "grid", "statement", "ingredients"}


@dataclass
class Decision:
    status: str  # contains | traces | absent | unknown
    basis: str | None
    evidence: str | None
    page: int | None
    conflict: bool
    sources: list[Evidence]


def fuse(evidence: list[Evidence], declarations: list[Evidence]) -> dict[str, Decision]:
    by: dict[str, list[Evidence]] = {a: [] for a in ALLERGENS}
    for ev in evidence:
        by[ev.allergen].append(ev)

    out: dict[str, Decision] = {}
    for a in ALLERGENS:
        items = by[a]
        direct = [e for e in items if e.rule in DIRECT_RULES]
        if direct:
            top = max(direct, key=lambda e: (SEVERITY[e.status], RULE_STRENGTH[e.rule]))
            statuses = {e.status for e in direct}
            conflict = ABSENT in statuses and bool(statuses & {CONTAINS, TRACES})
            out[a] = Decision(top.status, top.rule, top.snippet, top.page, conflict, items)
            continue
        glob = [e for e in items if e.rule == "global_statement"]
        if glob:
            g = glob[0]
            out[a] = Decision(ABSENT, g.rule, g.snippet, g.page, False, items)
            continue
        if declarations:
            d = declarations[0]
            out[a] = Decision(ABSENT, "implicit_declaration", d.snippet, d.page, False, items)
            continue
        out[a] = Decision("unknown", None, None, None, False, items)
    return out
