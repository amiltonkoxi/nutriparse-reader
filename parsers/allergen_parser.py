# legend: Extract allergen presence (contains/traces/absent) from raw text.

import re, json
from pathlib import Path
from unidecode import unidecode

RULES_PATH = Path(__file__).resolve().parent.parent / "rules" / "allergens.json"
RULES = json.loads(RULES_PATH.read_text(encoding="utf-8"))

TARGETS = ["gluten","egg","crustaceans","fish","peanut","soy","milk","tree_nuts","celery","mustard"]

def _normalize(s:str)->str:
    return re.sub(r"\s+"," ", unidecode((s or "")).lower())

def _match_any(pats, text):
    for p in pats or []:
        if re.search(p, text): return p
    return None

def parse_allergens(raw_text: str) -> dict:
    t = _normalize(raw_text)
    out = {}
    for k in TARGETS:
        r = RULES.get(k, {})
        ev = _match_any(r.get("contains"), t); st = "contains" if ev else None
        if not st: ev = _match_any(r.get("traces"), t);  st = "traces" if ev else None
        if not st: ev = _match_any(r.get("absent"), t);  st = "absent"  if ev else None
        out[k] = {"status": st or "unknown", "evidence": ev}
    return out
