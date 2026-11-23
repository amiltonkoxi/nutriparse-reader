"""Each test is one declaration format seen in real supplier sheets."""

from helpers import make_doc, make_page

from nutriparse.allergens import ALLERGENS, detect
from nutriparse.document import Document


def statuses(doc):
    return {a: d.status for a, d in detect(doc).items()}


def test_no_evidence_means_unknown_not_absent():
    # The v0.3 bug: silence was reported as "absent".
    s = statuses(make_doc(["Termék neve: Sertéskaraj", "Tárolás: 0-4 °C"]))
    assert set(s.values()) == {"unknown"}


def test_ingredient_list_yoghurt_regression():
    # v0.3 reported milk as absent for a natural yoghurt.
    s = statuses(make_doc(["3. ÖSSZETEVŐK", "Pasztőrözött tehéntej, kultúra.", "4. JELÖLÉS"]))
    assert s["milk"] == "contains"
    assert s["gluten"] == "unknown"


def test_ingredient_list_stops_at_next_sentence():
    s = statuses(make_doc([
        "Összetevők: csirkeszárny, búzaliszt, só (kakukkfű) A termék tartalmazhat tejet, zellert és szóját.",
    ]))
    assert s["gluten"] == "contains"
    assert s["milk"] == "traces" and s["celery"] == "traces" and s["soy"] == "traces"


def test_statements_contains_and_traces():
    s = statuses(make_doc([
        "Allergén információ: a termék tejet (tejfehérjét, laktózt) tartalmaz.",
        "Nyomokban mustárt tartalmazhat.",
    ]))
    assert s["milk"] == "contains"
    assert s["mustard"] == "traces"
    # an explicit declaration lists the allergens: the others are absent
    assert s["egg"] == "absent"
    assert detect(make_doc(["Allergén információ: hal."]))["egg"].basis == "implicit_declaration"


def test_global_statement():
    s = statuses(make_doc(["ALLERGÉN ANYAGOKAT NEM TARTALMAZ.", "GMO MENTES."]))
    assert set(s.values()) == {"absent"}
    s = statuses(make_doc(["ALERGENY / Brak alergenów w zakładzie"]))
    assert set(s.values()) == {"absent"}


def test_distractors_do_not_create_absence():
    # "free from foreign odours" next to "fish" is not an allergen statement
    s = statuses(make_doc(["Illat: jellegzetesen hal szagú, minden idegen szagtól mentes."]))
    assert s["fish"] == "unknown"


def test_table_row_containing_is_not_contains():
    # "Glutént tartalmazó" (containing gluten) is a row label, not a statement.
    s = statuses(make_doc(["Glutént tartalmazó gabonafélék és azokból készült termékek N"]))
    assert s["gluten"] == "absent"


def test_table_single_flag_and_wrapped_row():
    s = statuses(make_doc([
        "Allergén információk  Igen (I)/ Nem (N)/ Keresztszennyeződésként tartalmazhat (X) I/N/X",
        "Tej és az abból készült termékek (beleértve a laktózt) I",
        "Kén-dioxid és az SO2-ben kifejezett szulfitok 10 mg/kg összkoncentrációt",
        "N",
        "Mustár és a belőle készült termékek X",
    ]))
    assert s["milk"] == "contains"
    assert s["sulphites"] == "absent"
    assert s["mustard"] == "traces"  # X means cross contamination per the legend


def test_table_two_columns():
    s = statuses(make_doc([
        "Összetevők és azokból készült termékek  Igen/Nem  Véletlen megjelenés (igen/nem)",
        "Tej és származékai I Laktóz, tejfehérje -",
        "Tojás és származékai N N",
        "Szója és származékai N I",
    ]))
    assert s == {**s, "milk": "contains", "egg": "absent", "soy": "traces"}


def test_tick_box_glyphs_hu_and_pl():
    s = statuses(make_doc([
        "Tej és abból készült termékek mentes ☐ tartalmaz ☒ előfordulhat ☐",
        "Zeller és abból készült termékek mentes ☒ tartalmaz ☐ előfordulhat ☐",
        "Jaja i produkty pochodne nie zawiera ☐ zawiera ☐ może zawierać ☒",
    ]))
    assert s["milk"] == "contains" and s["celery"] == "absent" and s["egg"] == "traces"


def test_plus_minus_grid():
    s = statuses(make_doc([
        "A termék a következő allergéneket tartalmazza: glutén",
        "01 + milk protein/ tejfehérje 15 - Cocoa/ kakaó",
        "03 - Eggs/ tojás 20 - Peanuts/ földimogyoró",
        "06 + Gluten/ glutén 22 - Sesame/ szezám",
        "12 - Fish/ hal 36 - Mustard/mustármag",
        "+ tartalmaz/ tartalmazhat",
        "- mentes",
    ]))
    assert s["gluten"] == "contains"  # the statement is more specific than "+"
    assert s["milk"] == "traces"      # "+" only means contains OR may contain
    assert s["egg"] == "absent" and s["mustard"] == "absent"


def test_x_mark_table_uses_geometry():
    lines = [
        "Allergiát okozó anyagok Igen Nem Kereszt",
        "Tojás és tojásból készült termékek X",
        "Halak és halakból készült termékek X",
        "Tej és ezekből készült termékek X",
        "Zeller és ezekből készült termékek X",
    ]
    # Column headings at x = 400 / 460 / 520; each X sits under one of them.
    pos = {
        0: [("Allergiát", 20), ("okozó", 70), ("anyagok", 110), ("Igen", 400), ("Nem", 460), ("Kereszt", 520)],
        1: [("Tojás", 20), ("és", 50), ("tojásból", 65), ("készült", 110), ("termékek", 150), ("X", 405)],
        2: [("Halak", 20), ("és", 50), ("halakból", 65), ("készült", 110), ("termékek", 150), ("X", 465)],
        3: [("Tej", 20), ("és", 40), ("ezekből", 55), ("készült", 100), ("termékek", 140), ("X", 525)],
        4: [("Zeller", 20), ("és", 50), ("ezekből", 65), ("készült", 110), ("termékek", 150), ("X", 465)],
    }
    s = statuses(Document([make_page(lines, positions=pos)]))
    assert s["egg"] == "contains" and s["fish"] == "absent" and s["milk"] == "traces" and s["celery"] == "absent"


def test_conflict_keeps_safer_status_and_flags_it():
    d = detect(make_doc([
        "Összetevők: búzaliszt, víz, só.",
        "Glutént tartalmazó gabonafélék és azokból készült termékek N",
    ]))
    assert d["gluten"].status == "contains"
    assert d["gluten"].conflict is True


def test_every_result_has_evidence_or_is_unknown():
    d = detect(make_doc(["Allergén információ: a termék tejet tartalmaz.", "Összetevők: tej, kultúra."]))
    for a in ALLERGENS:
        assert (d[a].status == "unknown") == (d[a].evidence is None)
