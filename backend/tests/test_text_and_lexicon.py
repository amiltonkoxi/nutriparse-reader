import pytest

from nutriparse.allergens.lexicon import ALLERGENS, allergens_in
from nutriparse.text import CHECKED, UNCHECKED, norm


def test_fourteen_eu_allergens():
    assert len(ALLERGENS) == 14
    assert {"sesame", "sulphites", "lupin", "molluscs"} <= set(ALLERGENS)


@pytest.mark.parametrize("s", ["Összetevők: tőkehal", "Kén-dioxid — „E220”…", "Łubin ☒ ☐ µg", "ß"])
def test_norm_keeps_offsets(s):
    assert len(norm(s)) == len(s)


def test_norm_marks_tick_boxes():
    assert norm("mentes ☒ tartalmaz ☐") == f"mentes {CHECKED} tartalmaz {UNCHECKED}"


@pytest.mark.parametrize(
    "text, expected",
    [
        ("búzaliszt, tyúktojás, ivóvíz", {"gluten", "egg"}),
        ("pasztőrözött tehéntej, kultúra", {"milk"}),
        ("garnélarák, kékkagyló, tintahal", {"crustaceans", "molluscs"}),
        ("Földimogyoró (amerikai mogyoró)", {"peanut"}),
        ("mogyoró, kesudió, mandula", {"tree_nuts"}),
        ("tartósítószer (kén-dioxid)", {"sulphites"}),
        ("mąka pszenna, jaja, mleko", {"gluten", "egg", "milk"}),
        ("morszczuk (Merluccius capensis)", {"fish"}),
        ("csillagfürtliszt", {"lupin"}),
        ("wheat flour, sesame seeds, mustard", {"gluten", "sesame", "mustard"}),
    ],
)
def test_lexicon_finds(text, expected):
    assert allergens_in(norm(text)) == expected


@pytest.mark.parametrize(
    "text",
    [
        "kakaóvaj",            # cocoa butter is not milk
        "masło kakaowe",       # same, Polish
        "cocoa butter",
        "kókusztej",           # coconut milk
        "coconut milk",
        "Nádudvari Tejüzem",   # a dairy plant in a header is not an ingredient
        "szabály",             # contains 'zab' (oat) inside a word
        "sajtó",               # press, not cheese
        "halmaz",              # set, not fish
    ],
)
def test_lexicon_ignores(text):
    assert allergens_in(norm(text)) == set()


def test_sulphur_dioxide_is_not_a_nut():
    assert allergens_in(norm("Kén-dioxid és szulfitok")) == {"sulphites"}
