# legend: Extract allergen presence (contains/traces/absent) from raw text.

import re
import json
from pathlib import Path
from unidecode import unidecode

# Load allergen keyword rules
RULES_PATH = Path(__file__).resolve().parent.parent / "rules" / "allergens.json"
RULES = json.loads(RULES_PATH.read_text(encoding="utf-8"))

TARGETS = [
    "gluten", "egg", "crustaceans", "fish", "peanut",
    "soy", "milk", "tree_nuts", "celery", "mustard"
]

def _normalize(text: str) -> str:
    """Lowercase, remove accents, and collapse spaces."""
    text = unidecode(text or "").lower()
    return re.sub(r"\s+", " ", text)

def _match_any(patterns, text):
    """Return first regex pattern that matches."""
    for pat in patterns or []:
        if re.search(pat, text):
            return pat
    return None

def parse_allergens(raw_text: str) -> dict:
    """Return allergen classification dictionary."""
    text = _normalize(raw_text)
    results = {}

    for key in TARGETS:
        rule = RULES.get(key, {})
        evidence = None
        status = "unknown"

        if ev := _match_any(rule.get("contains"), text):
            status, evidence = "contains", ev
        elif ev := _match_any(rule.get("traces"), text):
            status, evidence = "traces", ev
        elif ev := _match_any(rule.get("absent"), text):
            status, evidence = "absent", ev

        results[key] = {"status": status, "evidence": evidence}

    return results
