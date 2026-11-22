"""Allergen detection: lexicon -> evidence rules -> fusion."""

from __future__ import annotations

import os

from ..document import Document
from ..extraction import render_page
from ..text import norm
from . import vision
from .fusion import Decision, fuse
from .lexicon import ALLERGENS, LABELS_EN
from .rules import (
    RX_ROW_PHRASE,
    RX_X_LEGEND,
    Context,
    Evidence,
    column_headers,
    rule_checkbox,
    rule_global,
    rule_grid,
    rule_ingredients,
    rule_layout_table,
    rule_statements,
    rule_table_flags,
)

# Switch used for the ablation study in docs/method.md.
VISION_ENABLED = os.getenv("NUTRIPARSE_DISABLE_VISION", "0") != "1"

__all__ = ["ALLERGENS", "LABELS_EN", "Decision", "Evidence", "detect", "collect_evidence"]


def collect_evidence(doc: Document) -> tuple[list[Evidence], list[Evidence]]:
    ctx = Context.build(doc)
    evidence: list[Evidence] = []
    grid_ev, grid_lines = rule_grid(ctx)
    evidence += grid_ev
    table_ev, rows_done = rule_table_flags(ctx, skip_lines=grid_lines)
    evidence += table_ev
    evidence += rule_checkbox(ctx)
    evidence += rule_layout_table(ctx, rows_done)
    for page in doc.pages:
        if not VISION_ENABLED:
            break
        if page.source == "text":
            # Digital page: tick boxes drawn as vector shapes leave no text.
            has_glyphs = any(e.rule == "checkbox" and e.page == page.number for e in evidence)
            if not has_glyphs and vision.tick_box_rows(page) and render_page(doc, page, dpi=200):
                evidence += vision.tick_boxes(page)
            continue
        evidence += vision.tick_boxes(page)
        seen = {e.allergen for e in evidence
                if e.page == page.number and e.rule in ("table_flags", "checkbox", "layout_table")}
        evidence += vision.flag_cells(page, skip=seen)
        seen = {e.allergen for e in evidence
                if e.page == page.number and e.rule in ("table_flags", "checkbox", "layout_table", "grid")}
        page_text = norm(" ".join(ln.text for ln in page.lines))
        # X-mark tables are read by geometry (rule_layout_table), not by OCR of row ends.
        if len(seen) < len(ALLERGENS) and _looks_like_table(page_text) and not column_headers(page):
            evidence += vision.row_tails(page, skip=seen, x_means_traces=bool(RX_X_LEGEND.search(page_text)))
    evidence += rule_ingredients(ctx)
    stmt_ev, declarations = rule_statements(ctx, table_lines=grid_lines | rows_done)
    evidence += stmt_ev
    evidence += rule_global(ctx)
    return evidence, declarations


def _looks_like_table(ntext: str) -> bool:
    """Several Annex II row phrases on the page ("... and products thereof")."""
    return len(RX_ROW_PHRASE.findall(ntext)) >= 4


def detect(doc: Document) -> dict[str, Decision]:
    evidence, declarations = collect_evidence(doc)
    return fuse(evidence, declarations)
