#Wire extraction engine and allergen parser; keep contract stable.

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import os, tempfile
from extractors.text_extractor import extract_text_from_pdf
from extractors.ocr_extractor import extract_text_via_ocr
from parsers.allergen_parser import parse_allergens

app = FastAPI(title="Food PDF Extractor API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: restrict on deploy
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/extract")
async def extract(file: UploadFile = File(...)):
    # save temp pdf
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        text = extract_text_from_pdf(tmp_path)
        mode = "text"
        if len((text or "").strip()) < 80:
            mode = "ocr"
            text = extract_text_via_ocr(tmp_path)

        allergens = parse_allergens(text or "")

        return {
            "meta": {
                "product_name": None,
                "source_file": file.filename,
                "extraction_mode": mode,
                "serving_basis": "per 100g",
                "languages": ["en", "hu", "pl"],
                "confidence": 0.75 if mode == "text" else 0.6,
            },
            "allergens": allergens,
            "nutrition": {
                "energy": {"kJ": None, "kcal": None},
                "fat_g": None,
                "carbohydrate_g": None,
                "sugar_g": None,
                "protein_g": None,
                "salt_g": None,
                "sodium_g": None,
                "notes": "values per 100g if available",
            },
            "extras": {"saturated_fat_g": None, "water_g": None, "collagen_g": None},
            "diagnostics": {"warnings": [], "pages_scanned": 0},
            "raw_text_preview": (text[:600] + ("…" if len(text) > 600 else "")) if text else None,
        }
    finally:
        os.unlink(tmp_path)
