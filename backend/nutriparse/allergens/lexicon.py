"""Multilingual lexicon for the 14 allergens of Regulation (EU) No 1169/2011,
Annex II, in Hungarian, English and Polish.

Patterns run on normalised text (see ``nutriparse.text.norm``): lower case,
no accents. ``(?<![a-z])`` marks the start of a word. Most patterns are
stems without a right boundary, because Hungarian adds case endings
(tej -> tejet, zeller -> zellert).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Order and keys follow Annex II. Keys are kept compatible with v0.3.
ALLERGENS: tuple[str, ...] = (
    "gluten",
    "crustaceans",
    "egg",
    "fish",
    "peanut",
    "soy",
    "milk",
    "tree_nuts",
    "celery",
    "mustard",
    "sesame",
    "sulphites",
    "lupin",
    "molluscs",
)

LABELS_EN: dict[str, str] = {
    "gluten": "Cereals containing gluten",
    "crustaceans": "Crustaceans",
    "egg": "Eggs",
    "fish": "Fish",
    "peanut": "Peanuts",
    "soy": "Soybeans",
    "milk": "Milk",
    "tree_nuts": "Tree nuts",
    "celery": "Celery",
    "mustard": "Mustard",
    "sesame": "Sesame",
    "sulphites": "Sulphur dioxide and sulphites",
    "lupin": "Lupin",
    "molluscs": "Molluscs",
}

W = r"(?<![a-z])"  # start of word

_PATTERNS: dict[str, list[str]] = {
    "gluten": [
        r"glut[ea]n", W + r"buza", W + r"tonkoly", W + r"rozs(?!da)", W + r"arpa", W + r"zab(?!al)",
        "kamut", "khorasan", "gabonafel", "wheat", W + r"rye\b", "barley", W + r"oats?\b",
        W + r"spelt", "pszen", W + r"zyto", "jeczmien", W + r"owies", "orkisz", W + r"zboz",
        "cereals? containing",
    ],
    "crustaceans": [
        "rakfel", "crustacea", "shellfish", "shrimp", "prawn", "garnela", "skorupia", "lobster",
        W + r"crab", "homar", "langusz",
    ],
    "egg": [W + r"tojas", "tyuktojas", W + r"eggs?\b", W + r"jaj(?:a|ka|ek|eczn)"],
    "fish": [
        W + r"hal(?:ak|akbol|bol|fele|faj|liszt|olaj|at|ra|hus)?(?![a-z])", "fish", W + r"ryb",
        "tonhal", "lazac", "tokehal", "hekk", "makrela", "szardell", "ancsovis", "anchov",
        "salmon", W + r"tuna\b", W + r"cod\b", W + r"hake", "pollock", "herring", W + r"trout",
        "mackerel", "pisztrang", "morszczuk", W + r"dorsz", W + r"losos", W + r"sledz", "pstrag",
        "mintaj", "tunczyk", W + r"makrel",
    ],
    "peanut": [
        "foldimogyor", "amerikai mogyor", "peanut", "arachid", r"orzesz\w* ziemn", r"orzech\w* ziemn",
        "groundnut",
    ],
    "soy": [W + r"szoja", W + r"soy", W + r"soja"],
    "milk": [
        W + r"tej(?!uzem)", "tehentej", "kecsketej", "juhtej", "laktoz", "lactose", W + r"(?<!coconut )(?<!almond )(?<!oat )(?<!soy )milk", "kazein",
        "casein", W + r"savo(?!ny)", W + r"vaj(?![a-z])", W + r"vajat", "tejszin", W + r"sajt(?!o)",
        W + r"turo(?![a-z])", "joghurt", "yogh?urt", W + r"jogurt", "kefir", r"(?<!cocoa )(?<!cacao )(?<!peanut )(?<!shea )butter", "cheese",
        W + r"cream", W + r"whey", r"mleko(?! kokos| owsian| sojow| migdal)", "mleczn", r"maslo(?! kakaow| orzech| shea)", "smietan", W + r"dairy",
    ],
    "tree_nuts": [
        r"diof[ea]l", W + r"dio(?![a-z])", W + r"diot\b", "kesudio", "pekandio", r"brazil ?dio",
        "mandula", r"(?<!foldi)(?<!amerikai )mogyoro", "pisztaci", "makadami", "csonthejas",
        r"tree ?nuts?", W + r"nuts?\b", "almond", "hazelnut", "walnut", "cashew", W + r"pecan",
        "pistachio", "macadamia", r"orzech(?!\w* ziemn)", W + r"migdal", "laskow",
    ],
    "celery": ["zeller", "celery", "celeriac", W + r"seler"],
    "mustard": ["mustar", "mustard", "gorczyc", "musztard"],
    "sesame": ["szezam", "sesame", W + r"sezam"],
    "sulphites": [
        r"ken-? ?dioxid", "szulfit", r"sul(?:ph|f)ite", r"sul(?:ph|f)ur dioxide", W + r"so2(?![0-9])",
        W + r"e ?22[0-8](?![0-9])", "dwutlenek siarki", "siarczyn", "diszulfit",
    ],
    "lupin": ["csillagfurt", W + r"lupin", W + r"lubin"],
    "molluscs": [
        "puhatestu", "mollus", "shellfish", "kagylo", "osztriga", W + r"csiga", "tintahal",
        W + r"polip", "oyster", "mussel", "squid", "octopus", "mieczak", W + r"malz",
    ],
}

COMPILED: dict[str, re.Pattern[str]] = {
    key: re.compile("|".join(f"(?:{p})" for p in pats)) for key, pats in _PATTERNS.items()
}


@dataclass(frozen=True)
class Mention:
    allergen: str
    start: int
    end: int


def find_mentions(ntext: str, start: int = 0, end: int | None = None) -> list[Mention]:
    """All allergen mentions in ``ntext[start:end]`` (normalised text),
    with offsets relative to ``ntext``. Sorted by position."""
    end = len(ntext) if end is None else end
    window = ntext[start:end]
    out: list[Mention] = []
    for key, rx in COMPILED.items():
        for m in rx.finditer(window):
            out.append(Mention(key, start + m.start(), start + m.end()))
    out.sort(key=lambda m: (m.start, m.allergen))
    return out


def allergens_in(ntext: str) -> set[str]:
    return {m.allergen for m in find_mentions(ntext)}
