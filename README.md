# Food PDF Extractor

**Automatic extraction of allergens and nutritional facts from unstructured food product PDFs (text or scanned).**  
Frontend: **Next.js (React)** • Backend: **FastAPI (Python)** • OCR: **Tesseract + PyPDFium2**

> *Developer Test Project – University of Debrecen (2025)*  
> **Instructor:** Dr. Tamás Bérczes • **Student:** Amilton Koxi

---

## 🔍 Overview

This web application extracts and structures data from **food product PDFs** (either digital or scanned), producing clean **JSON outputs** and interactive **tables** showing:

- **Allergens:** Gluten, Egg, Crustaceans, Fish, Peanut, Soy, Milk, Tree Nuts, Celery, Mustard  
- **Nutrition:** Energy, Fat, Carbohydrate, Sugar, Protein, Sodium

The backend automatically chooses between **text extraction** (PyPDFium2) and **OCR** (Tesseract), ensuring compatibility with any document type.

---

## ⚙️ Architecture

```text
Frontend (Next.js)
 └── Uploads PDF → calls FastAPI
Backend (FastAPI)
 ├── Text extraction (PyPDFium2)
 ├── OCR fallback (Tesseract)
 ├── Rule-based parsing (keywords / regex)
 └── Returns structured JSON
````

**Main Technologies**

* **Frontend:** Next.js (TypeScript, App Router)
* **Backend:** FastAPI (Python 3.12, Uvicorn)
* **OCR:** Tesseract via `pytesseract`
* **PDF Reader:** PyPDFium2
* **Parsing Rules:** `rules/allergens.json` and `rules/nutrition.json`

---

## 📁 Repository Structure

```text
food-pdf-extractor/
├─ backend/
│  ├─ main.py              # FastAPI app & endpoints
│  ├─ extractors/          # text_extractor.py, ocr_extractor.py
│  ├─ parsers/             # allergen_parser.py
│  ├─ rules/               # allergen and nutrition patterns
│  └─ requirements.txt
├─ frontend/
│  ├─ app/page.tsx         # Upload interface + results view
│  └─ next.config.ts
└─ samples/
   └─ test.pdf
```

---

## Getting Started

### Requirements

* **Python 3.12+**
* **Node.js 18+**
* **Tesseract OCR**
  Ubuntu: `sudo apt install tesseract-ocr tesseract-ocr-eng`

### Backend (FastAPI)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

uvicorn main:app --reload --host 127.0.0.1 --port 8000
# Health check → http://127.0.0.1:8000/health  -> {"status":"ok"}
```

Run test extraction:

```bash
curl -s -X POST "http://127.0.0.1:8000/api/extract" \
  -F "file=@./samples/test.pdf" | jq
```

### Frontend (Next.js)

```bash
cd frontend
npm install
echo "NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000" > .env.local
npm run dev
# Open http://localhost:3000
```

---

## 🧾 Example Output

### JSON Output (Backend Response)

```json
{
  "meta": {
    "source_file": "test.pdf",
    "extraction_mode": "text",
    "confidence": 0.75
  },
  "allergens": {
    "gluten": { "status": "absent", "evidence": "allergen anyagokat nem tartalmaz" },
    "milk":   { "status": "absent", "evidence": "allergen anyagokat nem tartalmaz" },
    "soy":    { "status": "unknown", "evidence": null }
  },
  "nutrition": {
    "energy_kJ": null,
    "fat_g": null,
    "protein_g": null
  }
}
```

### 📊 Structured Table (Frontend Visualization)

| Category      | Item        | Status  | Evidence                         |
| ------------- | ----------- | ------- | -------------------------------- |
| **Allergen**  | Gluten      | Absent  | allergen anyagokat nem tartalmaz |
| **Allergen**  | Milk        | Absent  | allergen anyagokat nem tartalmaz |
| **Allergen**  | Soy         | Unknown | —                                |
| **Nutrition** | Energy (kJ) | —       | values per 100g if available     |
| **Nutrition** | Fat (g)     | —       | values per 100g if available     |
| **Nutrition** | Protein (g) | —       | values per 100g if available     |

---

## 🧩 Interpretation

* **Backend (FastAPI):** Outputs machine-readable JSON.
* **Frontend (Next.js):** Renders the same data in a user-friendly table.
* Data remains synchronized and consistent between layers.
* Supports multilingual detection and scalable AI-based classification.

---

## 🔜 Roadmap

* Add **AI-based allergen detection (LLMs)**
* Improve OCR accuracy with **image preprocessing**
* Extend nutrition field coverage (fiber, salt, cholesterol, etc.)
* Deploy on **Render (backend)** and **Vercel (frontend)**
* Add **export formats** (JSON / CSV / PDF report)

---

## 📚 Credits

© 2025 – **Amilton Koxi**
*MSc Computer Science | University of Debrecen – Developer Test Projects 2025*
**Instructor:** Dr. Tamás Bérczes

