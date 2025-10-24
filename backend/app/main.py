from __future__ import annotations
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import tempfile, os, re
from unidecode import unidecode


# --- normalize allergens to an object (robust) ---
from typing import Any, Dict

def _normalize_allergens(a: Any) -> Dict[str, Any]:
    if not a:
        return {}
    if isinstance(a, dict):
        return a
    out: Dict[str, Any] = {}
    if isinstance(a, list):
        for item in a:
            # dict case
            if isinstance(item, dict):
                k = item.get("key") or item.get("name") or item.get("allergen") or item.get("k")
                v = item.get("value") or item.get("val") or item.get("status") or item.get("v")
                evid = item.get("evidence")
                if not k:
                    continue
                if isinstance(v, dict):
                    out[k] = v
                    if evid is not None:
                        out[k].setdefault("evidence", evid)
                else:
                    out[k] = {"status": v, "evidence": evid}
            # pair/tuple case
            elif isinstance(item, (list, tuple)) and len(item) >= 2:
                k, v = item[0], item[1]
                if isinstance(k, str):
                    if isinstance(v, dict):
                        out[k] = v
                    else:
                        out[k] = {"status": v}
    return out

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
        m = re.search(pat, text, flags=re.IGNORECASE)
        if m:
            candidate = re.sub(r"\s+", " ", m.group(1)).strip(" .:-")
            candidate_norm = candidate.lower()
            alpha_count = sum(ch.isalpha() for ch in candidate_norm)
            digit_count = sum(ch.isdigit() for ch in candidate)
            if (
                3 <= len(candidate) <= 80
                and candidate_norm not in _FIELD_MARKERS
                and len(candidate.split()) > 1
                and alpha_count >= 3
                and digit_count <= alpha_count + 2
                and not ("kg" in candidate_norm and "/" in candidate)
            ):
                return candidate.upper()

            # then scan following lines for the first meaningful text field
            remainder = text[m.end():]
            for line in remainder.splitlines():
                clean = re.sub(r"\s+", " ", line).strip(" .:-")
                if not clean:
                    continue
                norm = clean.lower()
                if norm in _FIELD_MARKERS:
                    continue
                if ":" in clean:
                    continue
                alpha = sum(ch.isalpha() for ch in norm)
                digit = sum(ch.isdigit() for ch in clean)
                if alpha < 3 or digit > alpha + 2:
                    continue
                words = clean.split()
                if len(words) <= 1 or len(words) > 12:
                    continue
                if "kg" in norm and "/" in clean:
                    continue
                return clean.upper()
    return None


def _guess_name_from_filename(filename: str | None) -> str | None:
    if not filename:
        return None
    stem = re.sub(r"\.[^.]+$", "", filename)
    stem = re.sub(r"^\d+[-_\s]*", "", stem)
    stem = stem.replace("_", " ").replace("-", " ")
    cleaned = re.sub(r"\s+", " ", stem).strip()
    if len(cleaned) < 3:
        return None
    return cleaned.upper()


from extractors.text_extractor import extract_text
from extractors.ocr_extractor import ocr_extract
from parsers.allergen_parser import parse_allergens
from parsers.nutrition_parser import parse_nutrition


# --- confidence helper (injected) ---
def compute_confidence(meta, allergens, nutrition):
    mode = (meta or {}).get("extraction_mode") or "text"
    base = 0.72 if mode == "text" else 0.64  # mode baseline

    # core macros present (kJ/kcal/fat/carbs/sugar/protein/salt|sodium)
    macros = []
    try:
        macros.extend([
            (nutrition or {}).get("energy_kJ"),
            (nutrition or {}).get("energy_kcal"),
            (nutrition or {}).get("fat_g"),
            (nutrition or {}).get("carbohydrate_g"),
            (nutrition or {}).get("sugars_g"),
            (nutrition or {}).get("protein_g"),
            (nutrition or {}).get("salt_g") or (nutrition or {}).get("sodium_mg"),
        ])
    except Exception:
        pass
    base += 0.02 * sum(1 for v in macros if v is not None)

    # allergens with known status
    try:
        base += 0.01 * sum(
            1 for k, v in (allergens or {}).items()
            if (v or {}).get("status") not in (None, "unknown")
        )
    except Exception:
        pass

    # clamp
    if base < 0.60: base = 0.60
    if base > 0.90: base = 0.90
    return round(base, 2)
# --- end helper ---


app = FastAPI(title="NutriParse Reader API", version="0.3.1")

# --- CORS config ---
_allowed_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "https://nutriparsereader.vercel.app,http://localhost:3000"
)
ALLOWED_ORIGINS = [origin.strip() for origin in _allowed_origins.split(",") if origin.strip()]
ALLOWED_ORIGIN_REGEX = os.getenv("ALLOWED_ORIGIN_REGEX", r"^https://.*vercel\.app$")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=ALLOWED_ORIGIN_REGEX,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)
# --- end CORS config ---

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/extract")
async def extract(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf_path = tmp.name
        tmp.write(await file.read())
    try:
        text = extract_text(pdf_path)
        mode = "text"
        if not text or len(text) < 200:
            text = ocr_extract(pdf_path)
            if text:
                mode = "ocr"

        t = text or ""
        t_norm = unidecode(t).lower()

        allergens_parsed = parse_allergens(t)
        allergens = _normalize_allergens(allergens_parsed)
        nutrition_values, nutrition_evidence, nutrition_note, serving_info = parse_nutrition(t)

        serving_basis = serving_info.get("basis") or "unknown"
        serving_basis_evidence = serving_info.get("evidence")
        serving_basis_inferred = bool(serving_info.get("inferred"))

        product_name_text = _extract_product_name(t)
        product_name_file = _guess_name_from_filename(file.filename)
        if product_name_file:
            if not product_name_text or len(product_name_text) > len(product_name_file) + 10:
                product_name = product_name_file
            else:
                product_name = product_name_text
        else:
            product_name = product_name_text

        # languages (simple heuristic)
        langs = []
        if any(w in t_norm for w in ["energy", "fat", "sugar", "milk", "soy"]): langs.append("en")
        if any(w in t_norm for w in ["energia", "zsir", "cukor", "tej", "szoja", "gluten"]): langs.append("hu")
        if any(w in t_norm for w in ["energia", "tluszcz", "cukry", "bialko", "sol", "soja"]): langs.append("pl")
        langs = list(dict.fromkeys(langs)) or ["en"]

        confidence = compute_confidence({"extraction_mode": mode}, allergens, nutrition_values)

        key_order = [
            "energy_kJ", "energy_kcal", "fat_g", "saturated_fat_g",
            "carbohydrate_g", "sugars_g", "protein_g", "salt_g", "sodium_mg",
        ]
        nutrient_presence = [
            nutrition_values.get(k) for k in key_order
        ]

        allergen_known = sum(1 for v in allergens.values() if (v or {}).get("status") not in (None, "unknown"))

        warnings = []
        if is_non_food(t):
            warnings.append("Document looks non-food (technical/chemical sheet); please confirm the input.")
        if not nutrition_note and all(val is None or (isinstance(val, str) and not str(val).strip()) for val in nutrient_presence):
            warnings.append("No nutrition values detected.")
        if allergen_known == 0:
            warnings.append("No explicit allergen statements detected.")

        # Move optional nutrient fields into extras with their evidence.
        extras_data: Dict[str, Any] = {}
        optional_fields = ["collagen_g", "water_g"]
        for field in optional_fields:
            value = nutrition_values.get(field)
            if value is None:
                continue
            extras_data[field] = {
                "value": value,
                "evidence": nutrition_evidence.get(field),
            }
            nutrition_values.pop(field, None)
            nutrition_evidence.pop(field, None)
        notes: list[str] = []
        if nutrition_note:
            notes.append(nutrition_note)

        diagnostics_payload = {
            "meta": {
                "product_name": product_name,
                "source_file": file.filename,
                "extraction_mode": mode,
                "serving_basis": serving_basis,
                "serving_basis_inferred": serving_basis_inferred,
                "languages": langs,
                "confidence": confidence
            },
            "allergens": allergens,
            "nutrition_per_100g": nutrition_values,
            "extras": extras_data,
            "diagnostics": {
                "warnings": warnings,
                "pages_scanned": (t.count("\n") // 40) if t else 0,
                "raw_text_preview": (t[:2000] if t else ""),
                "nutrition_evidence": nutrition_evidence,
                "serving_basis_evidence": serving_basis_evidence,
                "notes": notes or None,
            }
        }
        if not diagnostics_payload["diagnostics"]["notes"]:
            diagnostics_payload["diagnostics"].pop("notes", None)

        return diagnostics_payload
    finally:
        try: os.remove(pdf_path)
        except Exception: pass


# --- injected: non-food heuristic ---
def is_non_food(text: str) -> bool:
    """
    Simple heuristic to flag non-food (safety/chemical) sheets:
    presence of technical terms and lack of food terms.
    """
    nt = unidecode((text or "")).lower()
    tech = any(k in nt for k in [
        "ph ", "suruseg", "suruseg ", "sűrűség", "oldat", "tisztit", "tiszta folyadek",
        "feluletaktiv", "biocid", "vegyszer", "korrizio", "haboldoszer"
    ])
    food = any(k in nt for k in ["osszetevok", "összetevők", "tapert", "tápérték", "energia", "kcal", "kij"])
    return tech and not food
