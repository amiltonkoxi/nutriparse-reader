from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Tuple, Iterable, Optional

from unidecode import unidecode

Allergen = Dict[str, Dict[str, Any]]


_STATUS_PRIORITY = {"unknown": 0, "absent": 1, "contains": 2, "traces": 3}


def _status_tuple(ok: bool | None, evidence: str) -> Dict[str, Any]:
    if ok is True:
        status = "contains"
    elif ok is False:
        status = "absent"
    else:
        status = "unknown"
    return {"status": status, "evidence": evidence or None}


def _clip(text: str, max_len: int = 60) -> str:
    cleaned = re.sub(r"\s+", " ", (text or "").strip())
    if len(cleaned) <= max_len:
        return cleaned
    return cleaned[:max_len].rstrip(",.;:- ")


def _update_status(
    target: Dict[str, Dict[str, Any]],
    key: str,
    status: str,
    evidence: str,
    *,
    priority: Optional[int] = None,
) -> None:
    current = target.get(key) or {"status": "unknown", "evidence": None, "_priority": 0}
    current_priority = current.get("_priority", _STATUS_PRIORITY.get(current.get("status"), 0))
    new_priority = priority if priority is not None else _STATUS_PRIORITY.get(status, 0)
    if new_priority >= current_priority:
        target[key] = {"status": status, "evidence": evidence, "_priority": new_priority}


@lru_cache(maxsize=1)
def _load_rules() -> Tuple[Dict[str, Dict[str, list[re.Pattern]]], Dict[str, list[re.Pattern]]]:
    """Load and compile allergen patterns declared in rules/allergens.json."""
    rules_path = Path(__file__).resolve().parent.parent / "rules" / "allergens.json"
    with rules_path.open(encoding="utf-8") as fh:
        raw = json.load(fh)

    compiled: Dict[str, Dict[str, list[re.Pattern]]] = {}
    for allergen, groups in raw.items():
        if allergen == "_globals":
            continue
        compiled[allergen] = {
            kind: [re.compile(pat, re.IGNORECASE) for pat in groups.get(kind, [])]
            for kind in ("contains", "traces", "absent")
        }

    global_raw = raw.get("_globals", {})
    globals_compiled = {
        name: [re.compile(pat, re.IGNORECASE) for pat in patterns]
        for name, patterns in global_raw.items()
    }
    return compiled, globals_compiled


def _normalize(text: str | None) -> str:
    if not text:
        return ""
    normalized = unidecode(text).lower()
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized


def _scan_table(text: str) -> Dict[str, Dict[str, Any]]:
    """Detect tables that use I/N/X style markings (Igen/Nem/trace)."""
    labels = {
        "gluten": ("gluten",),
        "egg": ("tojas", "egg"),
        "crustaceans": ("rakfelek", "crustaceans"),
        "fish": ("hal", "fish"),
        "peanut": ("foldimogyoro", "peanut"),
        "soy": ("soja", "szoja", "soy"),
        "milk": ("tej", "lakt", "milk"),
        "tree_nuts": ("diofelek", "nuts", "tree nuts"),
        "celery": ("zeller", "celery"),
        "mustard": ("mustar", "mustard"),
    }

    table_hits: Dict[str, Dict[str, Any]] = {}
    for key, synonyms in labels.items():
        pattern = re.compile(
            rf"(?is)(?:{'|'.join(synonyms)})[^a-z0-9]{{0,80}}?(?:\b(i|igen|y)\b|\b(n|nem|no)\b|\b(x)\b)"
        )
        match = pattern.search(text)
        if not match:
            continue
        snippet = text[max(0, match.start() - 40): match.end() + 40].strip()
        context = text[max(0, match.start() - 5): min(len(text), match.end() + 15)]
        if "i/n/x" in context.replace(" ", "") or "igen nem" in context:
            continue
        if match.group(1):
            table_hits[key] = {"status": "contains", "evidence": snippet}
        elif match.group(2):
            table_hits[key] = {"status": "absent", "evidence": snippet}
        else:
            table_hits[key] = {"status": "traces", "evidence": snippet}
    return table_hits


_ALLERGEN_SYNONYMS: Dict[str, Tuple[str, ...]] = {
    "gluten": ("gluten", "buza", "wheat", "liszt"),
    "egg": ("egg", "tojas", "ovum"),
    "crustaceans": ("crustacean", "rakfelek", "shellfish", "prawn", "shrimp", "kagylo"),
    "fish": ("fish", "hal", "hekk"),
    "peanut": ("peanut", "foldimogyoro"),
    "soy": ("soy", "soja", "szoja"),
    "milk": ("milk", "tej", "lact", "tejfeherje", "lakt"),
    "tree_nuts": ("nut", "dio", "mandula", "hazelnut", "almond", "walnut", "pistachio", "cashew"),
    "celery": ("celery", "zeller"),
    "mustard": ("mustard", "mustar"),
}

_TRACE_KEYWORDS = (
    "nyomokban",
    "tartalmazhat",
    "may contain",
    "traces",
    "keresztszennyez",
)

_CONTAINS_KEYWORDS = (
    " tartalmaz ",
    " tartalmaz:",
    " contains ",
    " contains:",
    " zawiera ",
    " enthält ",
)

_ABSENT_KEYWORDS = (
    "nem tartalmaz",
    "mentes",
    "does not contain",
    "free from",
    "without",
    "frei von",
)


def _scan_explicit_lines(raw_text: str, out: Dict[str, Dict[str, Any]]) -> None:
    def _syn_match(norm: str, syn: str) -> bool:
        syn = syn.strip().lower()
        if not syn:
            return False
        pattern = re.escape(syn)
        return bool(re.search(rf"\b{pattern}(?:[a-z]{0,3})?\b", norm))

    lines = raw_text.splitlines()
    for line in lines:
        if not line.strip():
            continue
        norm = unidecode(line).lower()
        evidence = _clip(line)
        is_trace = any(keyword in norm for keyword in _TRACE_KEYWORDS)
        is_absent_kw = any(keyword in norm for keyword in _ABSENT_KEYWORDS)
        is_contains_kw = (
            any(keyword in norm for keyword in _CONTAINS_KEYWORDS)
            or norm.startswith("tartalmaz ")
            or norm.startswith("contains ")
        )

        for allergen, synonyms in _ALLERGEN_SYNONYMS.items():
            matched = False
            contains_strength = 0
            for syn in synonyms:
                pattern = rf"([+\-])\s*[^+\-]{{0,40}}{re.escape(syn.strip().lower())}"
                m = re.search(pattern, norm)
                if m:
                    sign = m.group(1)
                    status = "contains" if sign == "+" else "absent"
                    if status == "contains":
                        keywords = ("protein", "flour", "lact", "milk", "gluten")
                        priority = 5 if any(word in norm for word in keywords) else 3
                        contains_strength = max(contains_strength, priority)
                        _update_status(out, allergen, status, evidence, priority=priority)
                    else:
                        _update_status(out, allergen, status, evidence, priority=3)
                    matched = True
            if is_trace and any(_syn_match(norm, syn) for syn in synonyms):
                _update_status(out, allergen, "traces", evidence, priority=4)
            elif not matched and is_contains_kw and not is_absent_kw and any(_syn_match(norm, syn) for syn in synonyms):
                _update_status(out, allergen, "contains", evidence, priority=3)
            elif not matched and is_absent_kw and any(_syn_match(norm, syn) for syn in synonyms):
                _update_status(out, allergen, "absent", evidence, priority=3)


INGREDIENT_HINTS = (
    "osszet",
    "összetev",
    "ingredient",
    "ingredients",
    "termek megnevezese",
    "termek neve",
    "product name",
    "filé",
    "filet",
    "összetétel",
)


def _apply_ingredient_fallback(raw_text: str, out: Dict[str, Dict[str, Any]]) -> None:
    lines = raw_text.splitlines()
    for allergen, synonyms in _ALLERGEN_SYNONYMS.items():
        current = out.get(allergen, {})
        if (current or {}).get("status") == "contains":
            continue
        for line in lines:
            norm = unidecode(line).lower()
            if " - " in norm or norm.strip().startswith("-"):
                continue
            if any(keyword in norm for keyword in _TRACE_KEYWORDS):
                continue
            if not any(re.search(rf"\\b{re.escape(syn.strip().lower())}\\b", norm) for syn in synonyms if syn.strip()):
                continue
            if not any(hint in norm for hint in INGREDIENT_HINTS):
                continue
            _update_status(out, allergen, "contains", _clip(line), priority=4)
            break


def _apply_trace_sentences(raw_text: str, out: Dict[str, Dict[str, Any]]) -> None:
    lines = raw_text.splitlines()
    for line in lines:
        norm = unidecode(line).lower()
        if not any(keyword in norm for keyword in _TRACE_KEYWORDS):
            continue
        snippet = _clip(line)
        for allergen, synonyms in _ALLERGEN_SYNONYMS.items():
            if any(re.search(rf"\b{re.escape(syn.strip().lower())}(?:[a-z]{{0,3}})?\b", norm) for syn in synonyms if syn.strip()):
                _update_status(out, allergen, "traces", snippet, priority=4)
def _clip(text: str, max_len: int = 60) -> str:
    cleaned = re.sub(r"\s+", " ", (text or "").strip())
    if len(cleaned) <= max_len:
        return cleaned
    return cleaned[:max_len].rstrip(",.;:- ")


def _extract_snippet(text: str, start: int, end: int, radius: int = 70) -> str:
    return _clip(text[max(0, start - radius): min(len(text), end + radius)])


def _first_match(patterns: Iterable[re.Pattern], text: str) -> Tuple[re.Match | None, re.Pattern | None]:
    for pat in patterns:
        match = pat.search(text)
        if match:
            return match, pat
    return None, None


def _apply_rule_patterns(
    allergen: str,
    text: str,
    rules: Dict[str, Dict[str, list[re.Pattern]]],
) -> Optional[Dict[str, Any]]:
    rule_set = rules.get(allergen, {})
    order = ("contains", "traces", "absent")
    for status in order:
        match, pattern = _first_match(rule_set.get(status, []), text)
        if not match:
            continue
        snippet = _extract_snippet(text, match.start(), match.end())
        if status == "contains":
            window = text[max(0, match.start() - 40): min(len(text), match.end() + 40)]
            negators = ("nem", "mentes", "free", "does not", "no ", "nie", "bez", "sen", "sin", "nincs")
            traces_tokens = ("nyomokban", "may contain", "keresztszennyez", "traces", "tartalmazhat")
            if any(word in window for word in negators):
                continue
            if any(word in window for word in traces_tokens):
                return {"status": "traces", "evidence": snippet}
            if not any(keyword.strip() and keyword.strip() in window for keyword in _CONTAINS_KEYWORDS):
                continue
            synonyms = _ALLERGEN_SYNONYMS.get(allergen, ())
            norm_snippet = unidecode(snippet).lower()
            if not any(re.search(rf"\b{re.escape(syn.strip().lower())}\b", norm_snippet) for syn in synonyms if syn.strip()):
                continue
        return {"status": status, "evidence": snippet}
    return None


def parse_allergens(text: str) -> Allergen:
    """Combine table heuristics with per-allergen pattern dictionaries."""
    rules, global_rules = _load_rules()
    normalized = _normalize(text)

    out: Allergen = {key: {"status": "unknown", "evidence": None} for key in rules}

    _scan_explicit_lines(text, out)
    _apply_ingredient_fallback(text, out)
    _apply_trace_sentences(text, out)

    # First: explicit I/N/X table rows.
    normalized_no_colon = normalized.replace(":", " ")
    table_hits = _scan_table(normalized_no_colon)
    for key, value in table_hits.items():
        _update_status(out, key, value.get("status", "unknown"), value.get("evidence"))

    # Global statements such as "allergen anyagokat nem tartalmaz".
    no_allergen_match = None
    for pat in global_rules.get("no_allergens", []):
        match = pat.search(normalized)
        if match:
            no_allergen_match = match
            break
    if no_allergen_match:
        snippet = _extract_snippet(normalized, no_allergen_match.start(), no_allergen_match.end())
        for key in out:
            if out[key]["status"] in ("unknown", "absent"):
                out[key] = {"status": "absent", "evidence": snippet}

    for pat in global_rules.get("fish_line", []):
        match = pat.search(normalized)
        if match:
            snippet = _extract_snippet(normalized, match.start(), match.end())
            out["fish"] = {"status": "contains", "evidence": snippet}
            break

    # Next, run pattern rules for allergens still marked as unknown.
    for allergen in list(out.keys()):
        if out[allergen]["status"] != "unknown":
            continue
        result = _apply_rule_patterns(allergen, normalized_no_colon, rules)
        if result:
            _update_status(out, allergen, result["status"], result.get("evidence"))

    # Se ainda restar "unknown", assumir ausente.
    for key, value in list(out.items()):
        if value.get("status") == "unknown":
            out[key] = {"status": "absent", "evidence": None}
        else:
            value.pop("_priority", None)

    return out
