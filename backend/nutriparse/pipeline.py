"""End-to-end analysis of one PDF."""

from __future__ import annotations

import re
import time

from . import SCHEMA_VERSION, __version__
from .allergens import ALLERGENS, detect
from .document import Document
from .extraction import load
from .metadata import is_non_food, languages, product_name
from .nutrition import parse_nutrition
from .schemas import AllergenResult, Diagnostics, ExtractionResult, Meta
from .text import for_nutrition, norm

OPTIONAL_NUTRIENTS = ("collagen_g", "water_g")
_NUTRITION_HEADING = re.compile(
    r"tapertek|nutrition|wartosc odzywcza|wartosci odzywcze|energia\s*[\[(:]?\s*(?:kj|kcal|\d)|energy\s*[\[(:]?\s*(?:kj|kcal|\d)"
)


def nutrition_section(text: str) -> str:
    """Text from the nutrition panel onwards.

    The ingredient list often contains "só" (salt) or percentages, which the
    nutrition parser would otherwise read as values ("szezámmag (4%)" -> salt 4 g).
    """
    m = _NUTRITION_HEADING.search(text)
    return text[m.start():] if m else text


def analyze_document(doc: Document, filename: str | None = None,
                     timings: dict[str, float] | None = None) -> ExtractionResult:
    timings = dict(timings or {})
    t0 = time.perf_counter()
    raw = doc.text()
    ntext = norm(raw)
    warnings: list[str] = []

    non_food = is_non_food(ntext)
    allergens: dict[str, AllergenResult] = {}
    if non_food:
        warnings.append("Document looks like a non-food (technical or chemical) sheet. Allergens not assessed.")
        allergens = {a: AllergenResult(status="unknown", basis="not_food") for a in ALLERGENS}
    else:
        for a, d in detect(doc).items():
            allergens[a] = AllergenResult(
                status=d.status, evidence=d.evidence, basis=d.basis, page=d.page, conflict=d.conflict
            )
    timings["allergens"] = (time.perf_counter() - t0) * 1000

    t1 = time.perf_counter()
    nut_text = for_nutrition(raw)
    values, evidence, note, serving = parse_nutrition(nutrition_section(nut_text))
    extras: dict[str, dict] = {}
    for field in OPTIONAL_NUTRIENTS:
        if values.get(field) is not None:
            extras[field] = {"value": values.pop(field), "evidence": evidence.pop(field, None)}
        else:
            values.pop(field, None)
            evidence.pop(field, None)
    timings["nutrition"] = (time.perf_counter() - t1) * 1000

    unknown = [a for a, r in allergens.items() if r.status == "unknown"]
    conflicts = [a for a, r in allergens.items() if r.conflict]
    evidenced = [a for a, r in allergens.items() if r.status != "unknown"]
    if not non_food and unknown:
        warnings.append(f"No evidence for {len(unknown)} of 14 allergens: {', '.join(unknown)}. Check manually.")
    if conflicts:
        warnings.append(f"Conflicting statements for: {', '.join(conflicts)}. The safer status was kept.")
    if all(v is None for v in values.values()) and not note:
        warnings.append("No nutrition values detected.")
    if doc.ocr_pages:
        pages = ", ".join(map(str, doc.ocr_pages))
        noun = "Page" if len(doc.ocr_pages) == 1 else "Pages"
        verb = "was" if len(doc.ocr_pages) == 1 else "were"
        warnings.append(f"{noun} {pages} {verb} read with OCR (scanned). Verify key values against the PDF.")

    meta = Meta(
        schema_version=SCHEMA_VERSION,
        engine_version=__version__,
        product_name=product_name(nut_text, filename),
        source_file=filename,
        extraction_mode=doc.mode,  # type: ignore[arg-type]
        pages=doc.page_count,
        ocr_pages=doc.ocr_pages,
        languages=languages(ntext),
        serving_basis=serving.get("basis") or "unknown",
        serving_basis_inferred=bool(serving.get("inferred")),
        allergen_coverage=round(len(evidenced) / len(ALLERGENS), 3),
        needs_review=bool(unknown or conflicts) and not non_food,
    )
    diagnostics = Diagnostics(
        warnings=warnings,
        pages_scanned=doc.page_count,
        raw_text_preview=raw[:2000],
        nutrition_evidence=evidence,
        serving_basis_evidence=serving.get("evidence"),
        notes=[note] if note else None,
        timings_ms={k: round(v, 1) for k, v in timings.items()},
    )
    return ExtractionResult(meta=meta, allergens=allergens, nutrition_per_100g=values,
                            extras=extras, diagnostics=diagnostics)


def analyze_pdf(path: str, filename: str | None = None, force_ocr: bool = False) -> ExtractionResult:
    t0 = time.perf_counter()
    doc = load(path, force_ocr=force_ocr)
    return analyze_document(doc, filename, {"extraction": (time.perf_counter() - t0) * 1000})
