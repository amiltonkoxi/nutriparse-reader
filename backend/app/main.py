from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import os, tempfile

# Local modules
from extractors.text_extractor import extract_text, parse_nutrition
from extractors.ocr_extractor import ocr_extract
from parsers.allergen_parser import parse_allergens

# --- App setup ---
app = FastAPI(title="NutriParse Reader API", version="0.2.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: restrict on deploy
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Health check ---
@app.get("/health")
def health():
    return {"status": "ok"}

# --- Main endpoint ---
@app.post("/extract")
async def extract(file: UploadFile = File(...)):
    # Save temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        # 1) Try text extraction first; fallback to OCR if empty
        text = extract_text(tmp_path) or ""
        mode = "text"
        if len(text.strip()) < 80:
            mode = "ocr"
            text = ocr_extract(tmp_path) or ""

        # 2) Parse sections
        allergens = parse_allergens(text)
        nutrition = parse_nutrition(text)  # <-- new nutrition parser

        # 3) Return structured JSON (API contract stable)
        return {
            "meta": {
                "product_name": None,
                "source_file": file.filename,
                "extraction_mode": mode,
                "serving_basis": "per 100g",
                "languages": ["en", "hu", "pl"],
                "confidence": 0.75 if mode == "text" else 0.60,
            },
            "allergens": allergens,
            "nutrition": nutrition,
            "extras": {
                "saturated_fat_g": None,
                "water_g": None,
                "collagen_g": None,
            },
            "diagnostics": {
                "warnings": [],
                "pages_scanned": 0,
                "raw_text_preview": (text[:4000] if text else None),
            },
        }

    finally:
        # Clean temp file safely
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
