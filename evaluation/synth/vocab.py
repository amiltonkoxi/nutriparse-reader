"""Vocabulary for synthetic specification sheets (HU / EN / PL).

Written separately from the engine's lexicon on purpose: the benchmark
should test the engine, not repeat it.
"""

from __future__ import annotations

ALLERGENS = (
    "gluten", "crustaceans", "egg", "fish", "peanut", "soy", "milk",
    "tree_nuts", "celery", "mustard", "sesame", "sulphites", "lupin", "molluscs",
)

# Product archetypes: ingredients per language and the allergens they contain.
PRODUCTS = [
    {
        "name": {"hu": "4 tojásos száraztészta", "en": "Egg pasta", "pl": "Makaron jajeczny"},
        "ingredients": {
            "hu": ["búzaliszt", "tyúktojás (18%)", "ivóvíz"],
            "en": ["durum wheat semolina", "free range eggs (18%)", "water"],
            "pl": ["mąka pszenna", "jaja (18%)", "woda"],
        },
        "contains": {"gluten", "egg"},
    },
    {
        "name": {"hu": "Natúr joghurt", "en": "Natural yoghurt", "pl": "Jogurt naturalny"},
        "ingredients": {
            "hu": ["pasztőrözött tehéntej", "élőflóra"],
            "en": ["pasteurised whole milk", "live cultures"],
            "pl": ["mleko pasteryzowane", "żywe kultury bakterii"],
        },
        "contains": {"milk"},
    },
    {
        "name": {"hu": "Panírozott csirkeszárny", "en": "Breaded chicken wings", "pl": "Panierowane skrzydełka"},
        "ingredients": {
            "hu": ["csirkeszárny (70%)", "búzaliszt", "napraforgóolaj", "étkezési só", "fűszerpaprika"],
            "en": ["chicken wings (70%)", "wheat flour", "sunflower oil", "salt", "paprika"],
            "pl": ["skrzydełka z kurczaka (70%)", "mąka pszenna", "olej słonecznikowy", "sól", "papryka"],
        },
        "contains": {"gluten"},
    },
    {
        "name": {"hu": "Darált paprikakrém", "en": "Crushed paprika paste", "pl": "Pasta paprykowa"},
        "ingredients": {
            "hu": ["paprika (87%)", "étkezési só", "sűrítőanyag (xantángumi)", "étkezési sav (citromsav)"],
            "en": ["red pepper (87%)", "salt", "thickener (xanthan gum)", "acid (citric acid)"],
            "pl": ["papryka (87%)", "sól", "zagęstnik (guma ksantanowa)", "kwas cytrynowy"],
        },
        "contains": set(),
    },
    {
        "name": {"hu": "Mustáros kolbász", "en": "Mustard sausage", "pl": "Kiełbasa z gorczycą"},
        "ingredients": {
            "hu": ["sertéshús", "szalonna", "étkezési só", "mustármag", "fűszerek"],
            "en": ["pork", "pork fat", "salt", "mustard seeds", "spices"],
            "pl": ["mięso wieprzowe", "słonina", "sól", "gorczyca", "przyprawy"],
        },
        "contains": {"mustard"},
    },
    {
        "name": {"hu": "Mogyorós tejcsokoládé", "en": "Hazelnut milk chocolate", "pl": "Czekolada mleczna z orzechami"},
        "ingredients": {
            "hu": ["cukor", "kakaóvaj", "teljes tejpor", "mogyoró (12%)", "emulgeálószer (szójalecitin)"],
            "en": ["sugar", "cocoa butter", "whole milk powder", "hazelnuts (12%)", "emulsifier (soya lecithin)"],
            "pl": ["cukier", "masło kakaowe", "mleko w proszku pełne", "orzechy laskowe (12%)", "emulgator (lecytyna sojowa)"],
        },
        "contains": {"milk", "tree_nuts", "soy"},
    },
    {
        "name": {"hu": "Étcsokoládé 70%", "en": "Dark chocolate 70%", "pl": "Czekolada gorzka 70%"},
        "ingredients": {
            "hu": ["kakaómassza", "cukor", "kakaóvaj", "emulgeálószer (napraforgólecitin)", "vanília"],
            "en": ["cocoa mass", "sugar", "cocoa butter", "emulsifier (sunflower lecithin)", "vanilla"],
            "pl": ["miazga kakaowa", "cukier", "masło kakaowe", "emulgator (lecytyna słonecznikowa)", "wanilia"],
        },
        "contains": set(),
    },
    {
        "name": {"hu": "Szezámmagos kenyér", "en": "Sesame bread", "pl": "Chleb z sezamem"},
        "ingredients": {
            "hu": ["búzaliszt", "ivóvíz", "élesztő", "étkezési só", "szezámmag (4%)"],
            "en": ["wheat flour", "water", "yeast", "salt", "sesame seeds (4%)"],
            "pl": ["mąka pszenna", "woda", "drożdże", "sól", "sezam (4%)"],
        },
        "contains": {"gluten", "sesame"},
    },
    {
        "name": {"hu": "Fagyasztott hekkfilé", "en": "Frozen hake fillet", "pl": "Filet z morszczuka"},
        "ingredients": {
            "hu": ["hekk (Merluccius capensis) (90%)", "víz (jégmáz)"],
            "en": ["hake (Merluccius capensis) (90%)", "water (glaze)"],
            "pl": ["morszczuk (Merluccius capensis) (90%)", "woda (glazura)"],
        },
        "contains": {"fish"},
    },
    {
        "name": {"hu": "Bazsalikomos pesto", "en": "Basil pesto", "pl": "Pesto bazyliowe"},
        "ingredients": {
            "hu": ["bazsalikom", "napraforgóolaj", "kesudió", "keménysajt (tej)", "fokhagyma", "só"],
            "en": ["basil", "sunflower oil", "cashew nuts", "hard cheese (milk)", "garlic", "salt"],
            "pl": ["bazylia", "olej słonecznikowy", "orzechy nerkowca", "ser twardy (mleko)", "czosnek", "sól"],
        },
        "contains": {"tree_nuts", "milk"},
    },
    {
        "name": {"hu": "Száraz fehérbor", "en": "Dry white wine", "pl": "Wino białe wytrawne"},
        "ingredients": {
            "hu": ["szőlő", "tartósítószer (kén-dioxid)"],
            "en": ["grapes", "preservative (sulphur dioxide)"],
            "pl": ["winogrona", "konserwant (dwutlenek siarki)"],
        },
        "contains": {"sulphites"},
    },
    {
        "name": {"hu": "Tenger gyümölcsei mix", "en": "Seafood mix", "pl": "Mieszanka owoców morza"},
        "ingredients": {
            "hu": ["garnélarák (40%)", "kékkagyló (30%)", "tintahal (30%)"],
            "en": ["shrimps (40%)", "mussels (30%)", "squid (30%)"],
            "pl": ["krewetki (40%)", "małże (30%)", "kalmary (30%)"],
        },
        "contains": {"crustaceans", "molluscs"},
    },
    {
        "name": {"hu": "Csillagfürtös keksz", "en": "Lupin biscuits", "pl": "Herbatniki z łubinem"},
        "ingredients": {
            "hu": ["búzaliszt", "csillagfürtliszt (10%)", "cukor", "vaj"],
            "en": ["wheat flour", "lupin flour (10%)", "sugar", "butter"],
            "pl": ["mąka pszenna", "mąka z łubinu (10%)", "cukier", "masło"],
        },
        "contains": {"gluten", "lupin", "milk"},
    },
    {
        "name": {"hu": "Zelleres levesalap", "en": "Celery soup base", "pl": "Baza do zupy selerowej"},
        "ingredients": {
            "hu": ["zellergumó (45%)", "sárgarépa", "étkezési só", "burgonyakeményítő"],
            "en": ["celeriac (45%)", "carrot", "salt", "potato starch"],
            "pl": ["seler korzeniowy (45%)", "marchew", "sól", "skrobia ziemniaczana"],
        },
        "contains": {"celery"},
    },
    {
        "name": {"hu": "Sózott földimogyoró", "en": "Salted peanuts", "pl": "Orzeszki ziemne solone"},
        "ingredients": {
            "hu": ["földimogyoró (96%)", "napraforgóolaj", "étkezési só"],
            "en": ["peanuts (96%)", "sunflower oil", "salt"],
            "pl": ["orzeszki ziemne (96%)", "olej słonecznikowy", "sól"],
        },
        "contains": {"peanut"},
    },
    {
        "name": {"hu": "Friss sertéskaraj", "en": "Fresh pork loin", "pl": "Schab wieprzowy świeży"},
        "ingredients": {
            "hu": ["sertéskaraj (100%)"],
            "en": ["pork loin (100%)"],
            "pl": ["schab wieprzowy (100%)"],
        },
        "contains": set(),
    },
]

# Short allergen names used in statements.
SHORT = {
    "hu": {"gluten": "glutén", "crustaceans": "rákfélék", "egg": "tojás", "fish": "hal",
           "peanut": "földimogyoró", "soy": "szója", "milk": "tej", "tree_nuts": "diófélék",
           "celery": "zeller", "mustard": "mustár", "sesame": "szezámmag", "sulphites": "kén-dioxid",
           "lupin": "csillagfürt", "molluscs": "puhatestűek"},
    "en": {"gluten": "gluten", "crustaceans": "crustaceans", "egg": "egg", "fish": "fish",
           "peanut": "peanuts", "soy": "soya", "milk": "milk", "tree_nuts": "nuts",
           "celery": "celery", "mustard": "mustard", "sesame": "sesame", "sulphites": "sulphites",
           "lupin": "lupin", "molluscs": "molluscs"},
    "pl": {"gluten": "gluten", "crustaceans": "skorupiaki", "egg": "jaja", "fish": "ryby",
           "peanut": "orzeszki ziemne", "soy": "soja", "milk": "mleko", "tree_nuts": "orzechy",
           "celery": "seler", "mustard": "gorczyca", "sesame": "sezam", "sulphites": "siarczyny",
           "lupin": "łubin", "molluscs": "mięczaki"},
}

# Annex II table rows.
ROWS = {
    "hu": {
        "gluten": "Glutént tartalmazó gabonafélék és azokból készült termékek",
        "crustaceans": "Rákfélék és azokból készült termékek",
        "egg": "Tojás és abból készült termékek",
        "fish": "Halak és azokból készült termékek",
        "peanut": "Földimogyoró és abból készült termékek",
        "soy": "Szójabab és abból készült termékek",
        "milk": "Tej és abból készült termékek (beleértve a laktózt is)",
        "tree_nuts": "Diófélék és azokból készült termékek",
        "celery": "Zeller és abból készült termékek",
        "mustard": "Mustár és abból készült termékek",
        "sesame": "Szezámmag és abból készült termékek",
        "sulphites": "Kén-dioxid és szulfitok (10 mg/kg felett)",
        "lupin": "Csillagfürt és abból készült termékek",
        "molluscs": "Puhatestűek és azokból készült termékek",
    },
    "en": {
        "gluten": "Cereals containing gluten and products thereof",
        "crustaceans": "Crustaceans and products thereof",
        "egg": "Eggs and products thereof",
        "fish": "Fish and products thereof",
        "peanut": "Peanuts and products thereof",
        "soy": "Soybeans and products thereof",
        "milk": "Milk and products thereof (including lactose)",
        "tree_nuts": "Nuts and products thereof",
        "celery": "Celery and products thereof",
        "mustard": "Mustard and products thereof",
        "sesame": "Sesame seeds and products thereof",
        "sulphites": "Sulphur dioxide and sulphites (>10 mg/kg)",
        "lupin": "Lupin and products thereof",
        "molluscs": "Molluscs and products thereof",
    },
    "pl": {
        "gluten": "Zboża zawierające gluten i produkty pochodne",
        "crustaceans": "Skorupiaki i produkty pochodne",
        "egg": "Jaja i produkty pochodne",
        "fish": "Ryby i produkty pochodne",
        "peanut": "Orzeszki ziemne (arachidowe) i produkty pochodne",
        "soy": "Soja i produkty pochodne",
        "milk": "Mleko i produkty pochodne (łącznie z laktozą)",
        "tree_nuts": "Orzechy i produkty pochodne",
        "celery": "Seler i produkty pochodne",
        "mustard": "Gorczyca i produkty pochodne",
        "sesame": "Nasiona sezamu i produkty pochodne",
        "sulphites": "Dwutlenek siarki i siarczyny (>10 mg/kg)",
        "lupin": "Łubin i produkty pochodne",
        "molluscs": "Mięczaki i produkty pochodne",
    },
}

T = {  # template strings
    "hu": {
        "title": "TERMÉKSPECIFIKÁCIÓ", "name": "Termék neve", "maker": "Gyártó",
        "desc": "1. Termékleírás", "ingr": "2. Összetevők", "allerg": "3. Allergén információ",
        "nutri": "4. Átlagos tápérték 100 g termékben", "store": "5. Tárolás",
        "contains": ["A termék a következő allergéneket tartalmazza: {l}.", "Allergén információ: {l}.",
                     "Allergének: {l}."],
        "traces": ["Nyomokban {l} tartalmazhat.", "A termék nyomokban tartalmazhat: {l}."],
        "global": ["Allergén anyagot nem tartalmaz.", "A termék allergénmentes."],
        "yes": "Igen", "no": "Nem", "x_head": "Keresztszennyeződés", "present": "Összetevőként",
        "flags_head": "Jelen van (I/N)", "legend_inx": "I = tartalmaz, N = nem tartalmaz, (X) = keresztszennyeződésként tartalmazhat",
        "cb": ("mentes", "tartalmaz", "előfordulhat"),
        "grid_legend": "+ tartalmaz/ tartalmazhat   - mentes",
        "distract": ["Idegen szagtól és íztől mentes.", "GMO mentes.",
                     "Mesterséges színezéket nem tartalmaz.", "A csomagolóanyag élelmiszer-biztonsági szempontból megfelelő."],
        "nut": ["Energia", "Zsír", "amelyből telített zsírsavak", "Szénhidrát", "amelyből cukrok", "Fehérje", "Só"],
        "store_text": "Száraz, hűvös helyen tárolandó.", "dec": ",",
        "desc_text": "A termék a vonatkozó magyar és EU-s jogszabályoknak megfelel.",
    },
    "en": {
        "title": "PRODUCT SPECIFICATION", "name": "Product name", "maker": "Manufacturer",
        "desc": "1. Description", "ingr": "2. Ingredients", "allerg": "3. Allergen information",
        "nutri": "4. Nutrition information per 100 g", "store": "5. Storage",
        "contains": ["Contains: {l}.", "Allergens: {l}.", "This product contains {l}."],
        "traces": ["May contain traces of {l}.", "May contain: {l}."],
        "global": ["No allergens.", "This product is free from all allergens."],
        "yes": "Yes", "no": "No", "x_head": "Cross-contamination", "present": "As ingredient",
        "flags_head": "Present (Y/N)", "legend_inx": "Y = contains, N = does not contain, (X) = cross contamination",
        "cb": ("free", "contains", "may contain"),
        "grid_legend": "+ contains/ may contain   - free",
        "distract": ["Free from foreign odours and taste.", "GMO free.", "No artificial colours.",
                     "Packaging complies with Regulation (EC) 1935/2004."],
        "nut": ["Energy", "Fat", "of which saturates", "Carbohydrate", "of which sugars", "Protein", "Salt"],
        "store_text": "Store in a cool, dry place.", "dec": ".",
        "desc_text": "The product complies with the applicable EU food law.",
    },
    "pl": {
        "title": "SPECYFIKACJA PRODUKTU", "name": "Nazwa produktu", "maker": "Producent",
        "desc": "1. Opis", "ingr": "2. Składniki", "allerg": "3. Informacja o alergenach",
        "nutri": "4. Wartość odżywcza w 100 g", "store": "5. Przechowywanie",
        "contains": ["Zawiera: {l}.", "Alergeny: {l}."],
        "traces": ["Może zawierać: {l}.", "Produkt może zawierać śladowe ilości: {l}."],
        "global": ["Produkt nie zawiera alergenów.", "Brak alergenów."],
        "yes": "Tak", "no": "Nie", "x_head": "Zanieczyszczenie krzyżowe", "present": "Jako składnik",
        "flags_head": "Obecny (T/N)", "legend_inx": "I = zawiera, N = nie zawiera, (X) = może zawierać",
        "cb": ("nie zawiera", "zawiera", "może zawierać"),
        "grid_legend": "+ zawiera/ może zawierać   - nie zawiera",
        "distract": ["Wolny od obcych zapachów.", "Produkt bez GMO.", "Nie zawiera sztucznych barwników.",
                     "Opakowanie zgodne z rozporządzeniem (WE) 1935/2004."],
        "nut": ["Wartość energetyczna", "Tłuszcz", "w tym kwasy tłuszczowe nasycone", "Węglowodany",
                "w tym cukry", "Białko", "Sól"],
        "store_text": "Przechowywać w suchym i chłodnym miejscu.", "dec": ",",
        "desc_text": "Produkt jest zgodny z obowiązującymi przepisami UE.",
    },
}
