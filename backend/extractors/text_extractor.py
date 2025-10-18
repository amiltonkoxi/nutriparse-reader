from __future__ import annotations
import re
from typing import Dict, Any
from io import BytesIO

import pdfplumber
from rules.regex_patterns import NUTRITION_PATTERNS

__all__ = ["extract_text_from_pdf", "parse_nutrition"]

# -----------------------------
# Text extraction (PDF -> text)
# -----------------------------
def extract_text_from_pdf(path_or_bytes) -> str:
    """
    Extract selectable text from a PDF (no OCR).
    Accepts a file path or raw bytes/bytearray.
    """
    if isinstance(path_or_bytes, (bytes, bytearray)):
        bio = BytesIO(path_or_bytes)
        with pdfplumber.open(bio) as pdf:
            parts = [(p.extract_text() or "") for p in pdf.pages]
        return "\n".join(parts)
    else:
        with pdfplumber.open(path_or_bytes) as pdf:
            parts = [(p.extract_text() or "") for p in pdf.pages]
        return "\n".join(parts)

# ------------------------------------------------
# Nutrition parser (HU/EN) + tolerant fallbacks
# ------------------------------------------------
_COMPILED: Dict[str, re.Pattern[str]] = {
    k: re.compile(v, re.IGNORECASE | re.DOTALL) for k, v in NUTRITION_PATTERNS.items()
}

def _to_float(v: str | None) -> float | None:
    if not v:
        return None
    try:
        return float(v.replace(",", "."))
    except ValueError:
        return None

# ... imports and helpers unchanged ...

def parse_nutrition(raw_text: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "energy": {"kJ": None, "kcal": None},
        "fat_g": None, "carbohydrate_g": None, "sugar_g": None,
        "protein_g": None, "salt_g": None, "sodium_g": None,
        "notes": "values per 100g if available",
    }
    if not raw_text:
        return out

    txt = raw_text.lower()

    # --- energy (unchanged) ---
    m = _COMPILED["energy"].search(txt)
    if m:
        val = _to_float(m.group(2)); unit = (m.group(3) or "").lower()
        if unit == "kj": out["energy"]["kJ"] = val
        elif unit == "kcal": out["energy"]["kcal"] = val

    # --- grams fields (unchanged) ---
    for key in ("fat", "carbohydrate", "sugar", "protein"):
        m = _COMPILED[key].search(txt)
        if m: out[f"{key}_g"] = _to_float(m.group(2))

    # --- salt/sodium with unit handling (NEW) ---
    # Pattern groups:
    # 1: "só/salt" label, 2: value, 3: unit; OR 4: "nátrium/sodium" label, 5: value, 6: unit
    m = _COMPILED["salt"].search(txt)
    if m:
        salt_val = _to_float(m.group(2)) if len(m.groups()) >= 2 else None
        salt_unit = (m.group(3) or "").lower() if len(m.groups()) >= 3 else ""
        sod_val = _to_float(m.group(5)) if len(m.groups()) >= 5 else None
        sod_unit = (m.group(6) or "").lower() if len(m.groups()) >= 6 else ""

        # If we have explicit salt:
        if salt_val is not None:
            # mg → g
            if salt_unit == "mg":
                salt_val = round(salt_val / 1000.0, 3)
                out["notes"] += " (salt mg→g)"
            out["salt_g"] = salt_val

        # Else, if we only have sodium:
        elif sod_val is not None:
            # sodium mg → g
            if sod_unit == "mg":
                sod_val = round(sod_val / 1000.0, 3)
                out["notes"] += " (sodium mg→g)"
            out["sodium_g"] = sod_val
            if sod_val is not None:
                out["salt_g"] = round(sod_val * 2.54, 3)
                out["notes"] += " (salt from sodium×2.54)"

    # --- safety heuristic (rare scans): huge salt likely mg misread ---
    if out["salt_g"] is not None and out["salt_g"] > 50:
        out["salt_g"] = round(out["salt_g"] / 1000.0, 3)
        out["notes"] += " (auto mg→g)"

    # --- fallback lines (unchanged below) ---
    def _fallback(line: str, *keys: str) -> float | None:
        l = line.strip().lower()
        if any(k in l for k in keys):
            m = re.search(r"(-?\d+(?:[.,]\d+)?)", l)
            if m: return _to_float(m.group(1))
        return None

    if any(out[k] is None for k in ("fat_g","carbohydrate_g","sugar_g","protein_g","salt_g")):
        for line in txt.splitlines():
            if out["fat_g"] is None:
                out["fat_g"] = _fallback(line, "zsír", "zsir", "fat")
            if out["carbohydrate_g"] is None:
                out["carbohydrate_g"] = _fallback(line, "szénhidrát", "szenhidrat", "carbohydrate")
            if out["sugar_g"] is None:
                out["sugar_g"] = _fallback(line, "cukor", "sugar")
            if out["protein_g"] is None:
                out["protein_g"] = _fallback(line, "fehérje", "feherje", "protein")
            if out["salt_g"] is None and out["sodium_g"] is None:
                v = _fallback(line, "só", "so ", "salt")
                if v is not None: out["salt_g"] = v

    return out

