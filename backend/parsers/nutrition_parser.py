from __future__ import annotations
import re
from math import isnan
from typing import Dict, Any, Optional, Iterable, Tuple, Union
from unidecode import unidecode

# -------- utils --------
def _clean(text: str) -> str:
    t = text.lower()
    t = t.replace("\r", "\n").replace("\u00a0", " ")
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{2,}", "\n", t)
    return t

def _to_float(s: str | None) -> Optional[float]:
    if not s:
        return None
    try:
        return float(s.replace(",", "."))
    except Exception:
        return None

def _iter_numeric_candidates(label: str, text: str) -> Iterable[Tuple[str, Optional[str], bool, int, int, int, int, str]]:
    """Yield candidate (value, unit) pairs located near the requested label."""
    label_regex = re.compile(rf"(?<![a-z0-9])({label})(?![a-z0-9])", re.IGNORECASE)
    value_regex = re.compile(r"(-|[0-9]+(?:[.,][0-9]+)?)(?:\s*(g|mg))?", re.IGNORECASE)

    for match in label_regex.finditer(text):
        window = text[match.end(): match.end() + 80]
        value_match = value_regex.search(window)
        if not value_match:
            continue
        raw = value_match.group(1)
        unit = (value_match.group(2) or "").lower() or None
        segment_before_value = window[:value_match.start(1)]
        has_newline = "\n" in segment_before_value
        snippet = text[max(0, match.start() - 40): match.end() + value_match.end()]
        value_start = match.end() + value_match.start(1)
        value_end = match.end() + value_match.end(1)
        yield raw, unit, has_newline, match.start(), match.end(), value_start, value_end, snippet

def _clip_snippet(snippet: str, max_len: int = 60) -> str:
    cleaned = re.sub(r"\s+", " ", (snippet or "").strip())
    if len(cleaned) <= max_len:
        return cleaned
    return cleaned[:max_len].rstrip(",.;:- ")


_GE_PATTERNS = [
    r"nie\s+mniej\s+niz",
    r"no?\s+less\s+than",
    r"at\s+least",
    r"minimum",
    r"\bmin\.?\b",
    r"legalabb",
    r"mindestens",
    r">=\s*",
]

_LE_PATTERNS = [
    r"nie\s+wie(c|ę)cej\s+niz",
    r"no?\s+more\s+than",
    r"at\s+most",
    r"maximum",
    r"\bmax\.?\b",
    r"legfeljebb",
    r"hochstens",
    r"<=\s*",
]

_GE_REGEXES = [re.compile(pat) for pat in _GE_PATTERNS]
_LE_REGEXES = [re.compile(pat) for pat in _LE_PATTERNS]


def _format_number(value: float) -> str:
    return f"{value:.3f}".rstrip("0").rstrip(".")


def _format_operator_value(value: float, operator: str) -> str:
    return f"{operator}{_format_number(value)}"


def _detect_operator(context_before: str, context_after: str) -> Optional[str]:
    window = (context_before[-60:] + " " + context_after[:40]).lower()
    for reg in _GE_REGEXES:
        if reg.search(window):
            return ">="
    for reg in _LE_REGEXES:
        if reg.search(window):
            return "<="
    return None


def _extract_line_range(label: str, text: str, convert_mg: bool = True) -> Tuple[Optional[Union[float, str]], Optional[str]]:
    """Detect table rows with min/max values and return the derived value and snippet."""
    pattern = re.compile(label, re.I)
    for line in text.split("\n"):
        match = pattern.search(line)
        if not match:
            continue
        segment = line[match.end():]
        if not re.search(r"(?:/\s*100\s*g|\[g\])", line):
            continue
        segment = re.sub(r"(?:mg|g)\s*/\s*100\s*g", " ", segment)
        values = []
        raw_tokens = []
        for token in re.finditer(r"(-|[0-9]+(?:[.,][0-9]+)?)(?:\s*(mg|g))?", segment):
            raw = token.group(1)
            unit = (token.group(2) or "").lower() or None
            raw_tokens.append(raw)
            if raw == "-":
                values.append((None, unit))
            else:
                values.append((_to_float(raw), unit))
        if not values or (len(raw_tokens) < 2 and "-" not in raw_tokens):
            continue
        min_val = values[0] if len(values) > 0 else (None, None)
        max_val = values[1] if len(values) > 1 else (None, None)
        parts: list[str] = []
        if min_val[0] is not None:
            val = min_val[0]
            if convert_mg and min_val[1] == "mg":
                val = round(val / 1000.0, 6)
            parts.append(_format_operator_value(val, ">="))
        if max_val[0] is not None:
            val = max_val[0]
            if convert_mg and max_val[1] == "mg":
                val = round(val / 1000.0, 6)
            parts.append(_format_operator_value(val, "<="))
        if parts:
            return " & ".join(parts), _clip_snippet(line)
    return None, None


def _match_line_value(
    label_terms: Iterable[str],
    raw_lines: Iterable[str],
    *,
    units: Tuple[str, ...] = ("g", "mg"),
    convert_mg: bool = True,
    bounds: Optional[Tuple[float, float]] = None,
    dash_to_zero: bool = False,
    exclude_terms: Optional[Tuple[str, ...]] = None,
) -> Tuple[Optional[float], Optional[str]]:
    def _term_present(norm_line: str, term: str) -> bool:
        term = term.strip().lower()
        if not term:
            return False
        escaped = re.escape(term)
        return bool(re.search(rf"\b{escaped}\b", norm_line)) or f"{term}/" in norm_line

    for idx, line in enumerate(raw_lines):
        if not line.strip():
            continue
        norm_line = unidecode(line).lower()
        if not any(_term_present(norm_line, term) for term in label_terms):
            continue
        if exclude_terms and any(term in norm_line for term in exclude_terms):
            continue
        combined = line
        combined_norm = norm_line
        label_positions = [combined_norm.find(term) for term in label_terms if combined_norm.find(term) != -1]
        if not label_positions:
            continue
        label_pos = min(label_positions)
        best: Optional[Tuple[int, int, bool, float, str]] = None
        for match in re.finditer(r"([0-9]+(?:[.,][0-9]+)?)", combined):
            value = _to_float(match.group(1))
            if value is None:
                continue
            after = combined[match.end(): match.end() + 6].lower()
            before = combined[max(0, match.start() - 6): match.start()].lower()
            unit = None
            after_stripped = after.lstrip()
            if after_stripped.startswith("mg"):
                unit = "mg"
            elif after_stripped.startswith("kcal"):
                unit = "kcal"
            elif after_stripped.startswith("kj"):
                unit = "kj"
            elif (
                after_stripped.startswith("g")
                or after.startswith(" g")
                or after.startswith("g/")
                or "g/100" in after.replace("l00", "100")
                or "g/100" in before.replace("l00", "100")
                or before.endswith(" g")
            ):
                unit = "g"
            if unit is None and "g/100" in combined.replace("l00", "100"):
                unit = "g"
            if units and (unit is None or unit not in units + ("kj", "kcal")):
                continue
            if unit == "mg" and convert_mg:
                value = round(value / 1000.0, 6)
                unit = "g"
            if bounds and not (bounds[0] <= value <= bounds[1]):
                continue
            if match.start() > 0 and combined[max(0, match.start() - 1)] == "/":
                continue
            distance = abs(match.start() - label_pos)
            snippet = _clip_snippet(combined[max(0, match.start() - 20): match.end() + 20])
            is_dash = combined[max(0, match.start() - 2): match.start()].strip().startswith("-")
            priority = 0 if is_dash else 1
            if best is None or (priority, distance) < (best[0], best[1]):
                best = (priority, distance, is_dash, value, snippet)
        if best:
            _, _, is_dash, value, snippet = best
            if is_dash and units == ("g", "mg"):
                return f"<={_format_number(value)}", snippet
            return value, snippet
        if dash_to_zero and re.search(r"-\s*$", norm_line):
            return 0.0, _clip_snippet(line)
    return None, None


def _match_dash_line(
    label_terms: Iterable[str],
    raw_lines: Iterable[str],
    *,
    bounds: Optional[Tuple[float, float]] = None,
) -> Tuple[Optional[str], Optional[str]]:
    for line in raw_lines:
        norm = unidecode(line).lower()
        if not any(term in norm for term in label_terms):
            continue
        match = re.search(r"-\s*([0-9]+(?:[.,][0-9]+)?)", line)
        if not match:
            continue
        value = _to_float(match.group(1))
        if value is None:
            continue
        if bounds and not (bounds[0] <= value <= bounds[1]):
            continue
        return f"<={_format_number(value)}", _clip_snippet(line)
    return None, None


def _match_value(
    label: str,
    text: str,
    *,
    convert_mg: bool = True,
    dash_to_zero: bool = False,
) -> Tuple[Union[Optional[float], str], Optional[str]]:
    """Return the first numeric token bound to the label, keeping >= or <= operators when present."""
    fallback_range = None
    line_value, line_evidence = _extract_line_range(label, text, convert_mg=convert_mg)
    if line_value is not None:
        if isinstance(line_value, (int, float)) or (isinstance(line_value, str) and "&" not in line_value):
            return line_value, line_evidence
        fallback_range = (line_value, line_evidence)

    candidates = list(_iter_numeric_candidates(label, text))
    dash_found = any(c[0] and c[0].strip() == "-" for c in candidates)

    for allow_newline in (False, True):
        for raw_value, unit, has_newline, label_start, label_end, value_start, value_end, _snippet in candidates:
            if has_newline and not allow_newline:
                continue
            if not raw_value or raw_value.strip() == "-":
                continue
            if dash_found and allow_newline:
                continue
            val = _to_float(raw_value)
            if val is None:
                continue
            if convert_mg and unit == "mg":
                val = round(val / 1000.0, 3)
            operator = _detect_operator(
                text[max(0, label_start - 80): label_start],
                text[value_end: min(len(text), value_end + 40)],
            )
            if operator:
                return _format_operator_value(val, operator), _clip_snippet(text[max(0, label_start - 40): value_end + 10])
            return val, _clip_snippet(text[max(0, label_start - 40): value_end + 10])
    if dash_to_zero:
        dash_regex = re.compile(rf"({label})\s*[-–—]", re.IGNORECASE)
        dash_match = dash_regex.search(text)
        if dash_match:
            snippet = _clip_snippet(text[max(0, dash_match.start() - 20): dash_match.end() + 5])
            return 0.0, snippet

    if fallback_range:
        return fallback_range

    return None, None


NUTRIENT_LABELS = {
    "fat_g": ["zsir", "zsirtartalom", "fat"],
    "carbohydrate_g": ["szenhidrat", "carbohydrate"],
    "sugars_g": ["cukor", "cukrok", "sugar", "sugars"],
    "protein_g": ["feherje", "fehérje", "protein"],
    "salt_g": ["salt", "salt/so"],
    "sodium_mg": ["natrium", "sodium"],
    "collagen_g": ["kolagen", "kollagen", "collagen"],
    "water_g": ["viz", "water", "woda"],
    "saturated_fat_g": ["telitett", "kwasy nasycone", "saturated", "saturates", "gesattigte"],
}

NUTRIENT_EXCLUDES = {
    "protein_g": ("hanyad", "hanyados", "háanyad", "háanyados", "kotoszovetmentes", "legalabb", "ratio"),
}


NUTRIENT_BOUNDS = {
    "fat_g": (0.0, 100.0),
    "saturated_fat_g": (0.0, 100.0),
    "carbohydrate_g": (0.0, 100.0),
    "sugars_g": (0.0, 60.0),
    "protein_g": (0.0, 80.0),
    "salt_g": (0.0, 25.0),
    "sodium_mg": (0.0, 5000.0),
    "collagen_g": (0.0, 100.0),
    "water_g": (0.0, 100.0),
}


def _within_bounds(key: str, value: Union[float, str, None]) -> Union[float, str, None]:
    if value is None:
        return None
    bounds = NUTRIENT_BOUNDS.get(key)
    if not bounds:
        return value
    low, high = bounds
    if isinstance(value, (int, float)):
        return value if low <= float(value) <= high else None
    if isinstance(value, str):
        match = re.search(r"([0-9]+(?:[.,][0-9]+)?)", value)
        if match:
            numeric = _to_float(match.group(1))
            if numeric is not None and low <= numeric <= high:
                return value
        return None
    return value

def _extract_energy(text: str) -> Dict[str, Optional[float]]:
    """Extract pairs such as '1982 kJ / 479 kcal' even when spacing is messy."""
    kj = kcal = None
    evidence_kj = evidence_kcal = None
    m = re.search(r"([0-9]+(?:[.,][0-9]+)?)\s*k[jJ]\s*[/|,]?\s*([0-9]+(?:[.,][0-9]+)?)\s*kcal", text)
    if m:
        kj = _to_float(m.group(1))
        kcal = _to_float(m.group(2))
        snippet = _clip_snippet(text[max(0, m.start() - 20): m.end() + 20])
        evidence_kj = evidence_kcal = snippet
    else:
        m1 = re.search(r"([0-9]+(?:[.,][0-9]+)?)\s*k[jJ]", text)
        m2 = re.search(r"([0-9]+(?:[.,][0-9]+)?)\s*kcal", text)
        if m1:
            kj = _to_float(m1.group(1))
            evidence_kj = _clip_snippet(text[max(0, m1.start() - 20): m1.end() + 20])
        if m2:
            kcal = _to_float(m2.group(1))
            evidence_kcal = _clip_snippet(text[max(0, m2.start() - 20): m2.end() + 20])
    if kj is None:
        m = re.search(r"energia\s*\[\s*k[jJ]\s*\][^0-9\-]{0,60}([0-9]+(?:[.,][0-9]+)?)", text, re.I)
        if m:
            kj = _to_float(m.group(1))
            evidence_kj = _clip_snippet(text[max(0, m.start() - 20): m.end() + 20])
    if kcal is None:
        m = re.search(r"energia\s*\[\s*kcal\s*\][^0-9\-]{0,60}([0-9]+(?:[.,][0-9]+)?)", text, re.I)
        if m:
            kcal = _to_float(m.group(1))
            evidence_kcal = _clip_snippet(text[max(0, m.start() - 20): m.end() + 20])
    return (
        {"energy_kJ": kj, "energy_kcal": kcal},
        {"energy_kJ": evidence_kj, "energy_kcal": evidence_kcal},
    )


_SATURATED_PATTERNS = [
    r"amelyb[őo]l\s+tel[ií]tett\s+zs[ií]rsav(?:ak)?\s*[:=]?\s*([0-9]+(?:[.,][0-9]+)?)\s*g?",
    r"w\s+tym\s+kwasy\s+nasycone\s*[:=]?\s*([0-9]+(?:[.,][0-9]+)?)\s*g?",
    r"saturated\s+fat\s*[:=]?\s*([0-9]+(?:[.,][0-9]+)?)\s*g?",
    r"davon\s+ges[aä]ttigte\s+fetts[aä]uren\s*[:=]?\s*([0-9]+(?:[.,][0-9]+)?)\s*g?",
]
_SATURATED_REGEXES = [re.compile(pat, re.IGNORECASE) for pat in _SATURATED_PATTERNS]


def _match_saturated(text: str) -> Tuple[Optional[float], Optional[str]]:
    for pat in _SATURATED_REGEXES:
        m = pat.search(text)
        if not m:
            continue
        value = _to_float(m.group(1))
        if value is not None:
            return value, _clip_snippet(text[max(0, m.start() - 10): m.end() + 10])
    return None, None

# -------- main --------
def parse_nutrition(raw_text: str) -> Tuple[Dict[str, Union[float, str, None]], Dict[str, Optional[str]], Optional[str]]:
    """Parse nutrition panels in Hungarian/English text and noisy OCR output."""
    t = _clean(raw_text)
    raw_lines = raw_text.splitlines()

    values: Dict[str, Union[float, str, None]] = {
        "energy_kJ": None,
        "energy_kcal": None,
        "fat_g": None,
        "saturated_fat_g": None,
        "carbohydrate_g": None,
        "sugars_g": None,
        "protein_g": None,
        "salt_g": None,
        "sodium_mg": None,
        "collagen_g": None,
        "water_g": None,
    }
    evidence: Dict[str, Optional[str]] = {k: None for k in values}
    any_value = False
    note: Optional[str] = None

    energy_vals, energy_evid = _extract_energy(t)
    for key, val in energy_vals.items():
        values[key] = val
        evidence[key] = energy_evid.get(key)

    def _first_pass(key: str, *, dash=False, convert_mg=True, exclude=None) -> Tuple[Optional[float], Optional[str]]:
        labels = NUTRIENT_LABELS.get(key, [])
        return _match_line_value(
            labels,
            raw_lines,
            convert_mg=convert_mg,
            bounds=NUTRIENT_BOUNDS.get(key),
            dash_to_zero=dash,
            exclude_terms=NUTRIENT_EXCLUDES.get(key) if exclude is None else exclude,
        )

    fat, fat_ev = _first_pass("fat_g")
    if fat is None:
        fat, fat_ev = _match_value(r"zs[ií]r|fat", t)
    else:
        range_val, range_ev = _match_value(r"zs[ií]r|fat", t)
        if isinstance(range_val, str) and any(range_val.startswith(op) for op in (">=", "<=")):
            fat, fat_ev = range_val, range_ev or fat_ev

    carbs, carbs_ev = _first_pass("carbohydrate_g")
    if carbs is None:
        carbs, carbs_ev = _match_value(r"sz[eé]nhidr[aá]t|carbohydrate", t)
    else:
        range_val, range_ev = _match_value(r"sz[eé]nhidr[aá]t|carbohydrate", t)
        if isinstance(range_val, str) and any(range_val.startswith(op) for op in (">=", "<=")):
            carbs, carbs_ev = range_val, range_ev or carbs_ev

    sugar, sugar_ev = _first_pass("sugars_g")
    if sugar is None:
        sugar, sugar_ev = _match_value(r"cukor|cukrok|sugar", t)
    else:
        range_val, range_ev = _match_value(r"cukor|cukrok|sugar", t)
        if isinstance(range_val, str) and any(range_val.startswith(op) for op in (">=", "<=")):
            sugar, sugar_ev = range_val, range_ev or sugar_ev

    protein, protein_ev = _first_pass("protein_g", exclude=NUTRIENT_EXCLUDES.get("protein_g"))
    if protein is None:
        range_val, range_ev = _match_value(r"feh[eé]rje|protein", t)
        excludes = NUTRIENT_EXCLUDES.get("protein_g", ())
        if range_ev and any(term in range_ev.lower() for term in excludes):
            range_val = None
        if isinstance(range_val, str) and any(range_val.startswith(op) for op in (">=", "<=")):
            protein, protein_ev = range_val, range_ev or protein_ev
        elif range_val is not None:
            protein, protein_ev = range_val, range_ev
    else:
        range_val, range_ev = _match_value(r"feh[eé]rje|protein", t)
        excludes = NUTRIENT_EXCLUDES.get("protein_g", ())
        if range_ev and any(term in range_ev.lower() for term in excludes):
            range_val = None
        if isinstance(range_val, str) and any(range_val.startswith(op) for op in (">=", "<=")):
            protein, protein_ev = range_val, range_ev or protein_ev
        elif range_val is not None:
            protein, protein_ev = range_val, range_ev or protein_ev

    collagen, collagen_ev = _first_pass("collagen_g")
    range_val, range_ev = _match_value(r"kollag[eé]n|kolagen|collagen", t)
    if collagen is None:
        if isinstance(range_val, str) and any(range_val.startswith(op) for op in (">=", "<=")):
            collagen, collagen_ev = range_val, range_ev
    else:
        if isinstance(range_val, str) and any(range_val.startswith(op) for op in (">=", "<=")):
            collagen, collagen_ev = range_val, range_ev or collagen_ev

    water, water_ev = _first_pass("water_g")
    range_val, range_ev = _match_value(r"viz|woda|water", t)
    if water is None:
        if isinstance(range_val, str) and any(range_val.startswith(op) for op in (">=", "<=")):
            water, water_ev = range_val, range_ev
    else:
        if isinstance(range_val, str) and any(range_val.startswith(op) for op in (">=", "<=")):
            water, water_ev = range_val, range_ev or water_ev
    if water is None:
        dash_val, dash_ev = _match_dash_line(NUTRIENT_LABELS.get("water_g", []), raw_lines, bounds=NUTRIENT_BOUNDS.get("water_g"))
        if dash_val:
            water, water_ev = dash_val, dash_ev

    salt, salt_ev = _first_pass("salt_g", dash=True)
    if salt is None:
        salt, salt_ev = _match_value(r"s[oó]|salt", t, dash_to_zero=True)
    else:
        range_val, range_ev = _match_value(r"s[oó]|salt", t, dash_to_zero=True)
        if isinstance(range_val, str) and any(range_val.startswith(op) for op in (">=", "<=")):
            salt, salt_ev = range_val, range_ev or salt_ev

    sodium, sodium_ev = _first_pass("sodium_mg", convert_mg=False)
    if sodium is None:
        sodium, sodium_ev = _match_value(r"n[aá]trium|sodium", t, convert_mg=False)

    sat_fat, sat_ev = _first_pass("saturated_fat_g")
    if sat_fat is None:
        sat_fat, sat_ev = _match_saturated(t)

    def _assign(key: str, value: Union[float, str, None], evid: Optional[str]):
        nonlocal any_value
        bounded = _within_bounds(key, value)
        if bounded is None:
            values[key] = None
            evidence[key] = None
        else:
            values[key] = bounded
            evidence[key] = evid
            any_value = True

    _assign("fat_g", fat, fat_ev)
    _assign("carbohydrate_g", carbs, carbs_ev)
    _assign("sugars_g", sugar, sugar_ev)
    _assign("protein_g", protein, protein_ev)
    _assign("collagen_g", collagen, collagen_ev)
    _assign("water_g", water, water_ev)
    _assign("salt_g", salt, salt_ev)
    _assign("sodium_mg", sodium, sodium_ev)
    _assign("saturated_fat_g", sat_fat, sat_ev)

    # Propagate salt from sodium if missing and sodium provided numerically.
    if values["salt_g"] is None and isinstance(values["sodium_mg"], (int, float)):
        values["salt_g"] = round(float(values["sodium_mg"]) * 2.54 / 1000.0, 3)
        evidence["salt_g"] = evidence.get("sodium_mg")
        any_value = True

    # Ensure sugars do not exceed carbohydrates; fix common OCR omission of decimal comma.
    sugars_val = values.get("sugars_g")
    carbs_val = values.get("carbohydrate_g")
    if isinstance(sugars_val, (int, float)) and isinstance(carbs_val, (int, float)):
        while sugars_val is not None and sugars_val >= 10 and carbs_val is not None and sugars_val > carbs_val:
            sugars_val = round(sugars_val / 10.0, 3)
        values["sugars_g"] = sugars_val


    for optional_key in ("collagen_g", "water_g"):
        if values.get(optional_key) is None:
            values.pop(optional_key, None)
            evidence.pop(optional_key, None)

    if not any_value:
        for key in list(values.keys()):
            values[key] = None
            evidence[key] = None
        note = "No nutrition table detected"

    def _normalize_numeric(key: str, value: Union[float, str, None]) -> Union[float, str, None]:
        if value is None:
            return None
        if isinstance(value, str):
            return value
        if key in ("energy_kJ", "energy_kcal"):
            return float(round(value))
        if key == "sodium_mg":
            return float(round(value))
        return float(round(value, 1))

    normalized = {}
    for key, value in values.items():
        normalized[key] = _normalize_numeric(key, value)

    return normalized, evidence, note
