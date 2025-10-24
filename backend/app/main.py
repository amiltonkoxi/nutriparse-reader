from __future__ import annotations

import os
import re
import tempfile
from typing import Any, Dict, List

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from unidecode import unidecode

from extractors.ocr_extractor import ocr_extract
from extractors.text_extractor import extract_text
from parsers.allergen_parser import parse_allergens
from parsers.nutrition_parser import parse_nutrition


def _normalize_allergens(payload: Any) -> Dict[str, Dict[str, Any]]:
    if not payload:
        return {}
    if isinstance(payload, dict):
        return payload

    normalized: Dict[str, Dict[str, Any]] = {}
    if isinstance(payload, list):
        for item in payload:
            if isinstance(item, dict):
                key = item.get("key") or item.get("name") or item.get("allergen")
                value = item.get("value") or item.get("status")
                evidence = item.get("evidence")
                if not key:
                    continue
                if isinstance(value, dict):
                    entry = dict(value)
                else:
                    entry = {"status": value}
                if evidence:
                    entry.setdefault("evidence", evidence)
                normalized[key] = entry
            elif isinstance(item, (list, tuple)) and len(item) >= 2:
                key, value = item[0], item[1]
                if isinstance(key, str):
                    if isinstance(value, dict):
                        normalized[key] = dict(value)
                    else:
                        normalized[key] = {"status": value}
    return normalized


_FIELD_MARKERS = {
    "tomeg",
    "csomagolas",
    "kategoria",
    "alkategoria",
    "logisztika",
    "gyartja",
    "forgalmazza",
    "ean",
    "cikkszam",
    "termek meghatarozasa",
    "osszetetel",
    "erzekszervi jellemzok",
    "fizikai es kemiai jellemzok",
    "alergen es egyeb informaciok",
}


def _extract_product_name(text: str) -> str | None:
    if not text:
        return None

    patterns = [
        r"(?:^|[\n\r])\s*(?:\d+\.\s*)?(?:a\s+termek neve|termek neve|termek megnevezese|megnevezes|product name)\s*[:\-]\s*([^\n\r]{3,80})",
    ]
    for pat in patterns:
        match = re.search(pat, text, flags=re.IGNORECASE)
        if not match:
            continue
        candidate = re.sub(r"\s+", " ", match.group(1)).strip(" .:-")
        norm = candidate.lower()
        alpha = sum(c.isalpha() for c in norm)
        digits = sum(c.isdigit() for c in candidate)
        if (
            3 <= len(candidate) <= 80
            and norm not in _FIELD_MARKERS
            and len(candidate.split()) > 1
            and alpha >= 3
            and digits <= alpha + 2
            and not ("kg" in norm and "/" in candidate)
        ):
            return candidate.upper()

        remainder = text[match.end():]
        for line in remainder.splitlines():
            cleaned = re.sub(r"\s+", " ", line).strip(" .:-")
            if not cleaned:
                continue
            norm_line = cleaned.lower()
            if norm_line in _FIELD_MARKERS:
                continue
            if ":" in cleaned:
                continue
            alpha_line = sum(ch.isalpha() for ch in norm_line)
            digits_line = sum(ch.isdigit() for ch in cleaned)
            words = cleaned.split()
            if (
                alpha_line >= 3
                and digits_line <= alpha_line + 2
                and 1 < len(words) <= 12
                and not ("kg" in norm_line and "/" in cleaned)
            ):
                return cleaned.upper()
    return None


def _guess_name_from_filename(filename: str | None) -> str | None:
    if not filename:
        return None
    stem = re.sub(r"\.[^.]+$", "", filename)
    stem = re.sub(r"^\d+[-_\s]*", "", stem)
    stem = stem.replace("_", " ").replace("-", " ")
    cleaned = re.sub(r"\s+", " ", stem).strip()
    return cleaned.upper() if len(cleaned) >= 3 else None


def compute_confidence(mode: str, allergens: Dict[str, Dict[str, Any]], nutrition: Dict[str, Any]) -> float:
    base = 0.72 if mode == "text" else 0.64
    keys = [
        "energy_kJ",
        "energy_kcal",
        "fat_g",
        "carbohydrate_g",
        "sugars_g",
        "protein_g",
        "salt_g",
        "sodium_mg",
    ]
    base += 0.02 * sum(1 for k in keys if nutrition.get(k) is not None)
    base += 0.01 * sum(1 for v in allergens.values() if (v or {}).get("status") not in (None, "unknown"))
    return round(min(max(base, 0.60), 0.90), 2)


_PER_100_G = re.compile(r"(?:per|/)\s*100\s*g|100\s*g\b|100g\b", re.I)
_PER_100_ML = re.compile(r"(?:per|/)\s*100\s*ml|100\s*ml\b|100ml\b", re.I)
_PER_PORTION = re.compile(r"(?:per\s+(?:portion|serving)|adagonkent)", re.I)


app = FastAPI(title="NutriParse Reader API", version="0.3.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/extract")
async def extract(file: UploadFile = File(...)) -> Dict[str, Any]:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf_path = tmp.name
        tmp.write(await file.read())

    try:
        text = extract_text(pdf_path) or ""
        mode = "text"
        if len(text) < 200:
            ocr_text = ocr_extract(pdf_path)
            if ocr_text:
                text = ocr_text
                mode = "ocr"

        normalized_text = unidecode(text).lower()
        allergens_raw = parse_allergens(text)
        allergens = _normalize_allergens(allergens_raw)
        nutrition_values, nutrition_evidence, nutrition_note = parse_nutrition(text)

        if _PER_100_G.search(normalized_text):
            serving_basis = "per 100g"
        elif _PER_100_ML.search(normalized_text):
            serving_basis = "per 100ml"
        elif _PER_PORTION.search(normalized_text):
            serving_basis = "per portion"
        else:
            serving_basis = "unknown"

        product_name_text = _extract_product_name(text)
        product_name_file = _guess_name_from_filename(file.filename)
        product_name = product_name_text or product_name_file

        langs: List[str] = []
        if any(token in normalized_text for token in ["energy", "fat", "sugar", "milk", "soy"]):
            langs.append("en")
        if any(token in normalized_text for token in ["energia", "zsir", "cukor", "tej", "szoja", "gluten"]):
            langs.append("hu")
        if any(token in normalized_text for token in ["energia", "tluszcz", "cukry", "bialko", "sol", "soja"]):
            langs.append("pl")
        if not langs:
            langs.append("en")
        langs = list(dict.fromkeys(langs))

        confidence = compute_confidence(mode, allergens, nutrition_values)

        diagnostics = {
            "warnings": [],
            "pages_scanned": normalized_text.count("\n") // 40 if text else 0,
            "raw_text_preview": text[:2000] if text else "",
            "nutrition_evidence": nutrition_evidence,
            "notes": [nutrition_note] if nutrition_note else None,
        }

        return {
            "meta": {
                "product_name": product_name,
                "source_file": file.filename,
                "extraction_mode": mode,
                "serving_basis": serving_basis,
                "languages": langs,
                "confidence": confidence,
            },
            "allergens": allergens,
            "nutrition_per_100g": nutrition_values,
            "extras": {},
            "diagnostics": diagnostics,
        }
    finally:
        try:
            os.remove(pdf_path)
        except Exception:
            pass
