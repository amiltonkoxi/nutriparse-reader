# Nutrition regex patterns (EN/HU, tolerant)
NUTRITION_PATTERNS = {
    "energy":       r"\b(energia|energy|energiatartalom)\b.*?(\d+(?:[.,]\d+)*)\s*(kcal|kj)",

    "fat":          r"\b(zs[ií]r|fat)\b[^0-9]{0,40}(\d+(?:[.,]\d+)?)(?:\s*g\b)?",
    "carbohydrate": r"\b(sz[eé]nhidr[aá]t|carbohydrate)\b[^0-9]{0,40}(\d+(?:[.,]\d+)?)(?:\s*g\b)?",
    "sugar":        r"\b(cukor|sugar)\b[^0-9]{0,40}(\d+(?:[.,]\d+)?)(?:\s*g\b)?",
    "protein":      r"\b(feh[eé]rje|protein)\b[^0-9]{0,40}(\d+(?:[.,]\d+)?)(?:\s*g\b)?",

    # Capture unit for salt/sodium as g or mg (group 3 / 6)
    "salt": (
        r"\b(s[oó]|salt)\b[^0-9]{0,40}(\d+(?:[.,]\d+)?)(?:\s*(g|mg)\b)?|"
        r"\b(n[aá]trium|sodium)\b[^0-9]{0,40}(\d+(?:[.,]\d+)?)(?:\s*(g|mg)\b)?"
    ),
}
