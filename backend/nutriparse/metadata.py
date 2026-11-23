"""Document metadata: product name, languages and a non-food check."""

from __future__ import annotations

import re

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


def product_name_from_text(text: str) -> str | None:
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


def product_name_from_filename(filename: str | None) -> str | None:
    if not filename:
        return None
    stem = re.sub(r"\.[^.]+$", "", filename)
    stem = re.sub(r"^\d+[-_\s]*", "", stem)
    stem = stem.replace("_", " ").replace("-", " ")
    cleaned = re.sub(r"\s+", " ", stem).strip()
    if len(cleaned) < 3:
        return None
    return cleaned.upper()


def product_name(text_for_nutrition: str, filename: str | None) -> str | None:
    """Prefer the name printed in the document unless it looks like noise."""
    from_text = product_name_from_text(text_for_nutrition)
    from_file = product_name_from_filename(filename)
    if from_file and (not from_text or len(from_text) > len(from_file) + 10):
        return from_file
    return from_text or from_file


_LANG_HINTS = {
    "hu": ("osszetevok", "tapertek", "energia", "zsir", "feherje", "termek", "tartalmaz", "allergen"),
    "en": ("ingredients", "energy", "protein", "product", "contains", "allergen", "nutrition"),
    "pl": ("skladniki", "bialko", "tluszcz", "produkt", "zawiera", "alergen", "wartosc odzywcza"),
}


def languages(ntext: str) -> list[str]:
    """Languages with at least two hint words, most frequent first."""
    scores = {lang: sum(ntext.count(w) for w in hints) for lang, hints in _LANG_HINTS.items()}
    ranked = [lang for lang, sc in sorted(scores.items(), key=lambda kv: -kv[1]) if sc >= 2]
    return ranked or ["unknown"]


_TECH = ("ph ", "suruseg", "oldat", "tisztit", "feluletaktiv", "biocid", "vegyszer", "korrozio",
         "detergent", "cleaning agent", "safety data sheet", "biztonsagi adatlap")
_FOOD = ("osszetevo", "tapertek", "energia", "kcal", "ingredient", "nutrition", "skladnik",
         "elelmiszer", "food")


def is_non_food(ntext: str) -> bool:
    """Technical or chemical sheet with no food vocabulary."""
    return any(k in ntext for k in _TECH) and not any(k in ntext for k in _FOOD)
