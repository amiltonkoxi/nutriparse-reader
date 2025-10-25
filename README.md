<h1 align="center">NutriParse Reader</h1>

<p align="center">
  Developer Test Project · University of Debrecen · 2025
</p>

---

## Project Overview

NutriParse Reader is a full-stack web application that automatically extracts allergen statements and nutrition facts from food product PDFs. Both digitally generated PDFs and scanned/image-based PDFs are supported. The backend uses AI-augmented parsing (rule-based extraction with LLM assistance) to detect allergens and nutrition values, while the frontend presents the results in both table and JSON formats for quick review.

---

## Features

- Upload up to **two PDFs per run** using drag and drop or a file picker.
- Backend processing with AI/LLM logic to interpret ingredient statements and nutrition tables.
- Extraction of the **10 required allergens**: Gluten, Egg, Crustaceans, Fish, Peanut, Soy, Milk, Tree nuts, Celery, Mustard.
- Extraction of the **6 nutrition values**: Energy, Fat, Carbohydrate, Sugar, Protein, Sodium.
- Structured output in a responsive **table view** plus a raw **JSON view**.
- Automatic **OCR fallback** for scanned or photo-based PDFs.

---

## Tech Stack

| Layer     | Technologies |
|-----------|--------------|
| Frontend  | Next.js (React), Tailwind CSS |
| Backend   | FastAPI (Python) |
| OCR       | Tesseract via `pytesseract` |
| Parsing   | Custom allergen & nutrition parsers with LLM assistance |

---

## Installation and Usage

1. **Clone the repository**
   ```bash
   git clone https://github.com/amiltonkoxi/nutriparse-reader.git
   cd nutriparse-reader
   ```

2. **Install backend dependencies**
   ```bash
   cd backend
   python3 -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Start the backend**
   ```bash
   uvicorn app.main:app --reload
   ```

4. **Install frontend dependencies**
   ```bash
   cd ../frontend
   npm install
   echo "NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000" > .env.local
   ```

5. **Start the frontend**
   ```bash
   npm run dev
   ```

6. **Open the app**
   Visit `http://localhost:3000` in your browser, upload up to two PDFs, and inspect the extracted data.

---

## Deployment

NutriParse Reader runs with a split deployment: the backend is hosted on Render, and the frontend is served by Vercel.

- **Backend:** https://nutriparse-reader-1.onrender.com  
- **Frontend:** https://nutriparsereader.vercel.app

Environment variables:

- **Render:** `ALLOWED_ORIGINS=https://nutriparsereader.vercel.app,http://localhost:3000`
- **Vercel:** `NEXT_PUBLIC_API_BASE=https://nutriparse-reader-1.onrender.com`

---

## Screenshots

| Preview | Description |
|---------|-------------|
| ![Homepage](image/Dark.png) | Homepage with upload panel and queue. |
| ![File Drop](image/filedrop.png) | Drag and drop queue with two files selected. |
| ![Extraction Result](image/result.png) | Extraction results with summary, JSON, and preview tabs. |

---

## Demo Video

Watch a short demonstration of NutriParse Reader in action:  
[![Demo Video](image/result.png)](image/Live_test.MOV)
*Consider replacing the thumbnail with a representative frame from the demo if available.*

---

## Deliverables Mapping

| Assignment Deliverable | Status |
|------------------------|--------|
| Source code            | ✔️ Completed in this repository (frontend and backend). |
| Documentation          | ✔️ Completed project overview and technical guides in this README. |
| Demonstration video    | ✔️ Completed in the “Demo Video” section. |
| Live deployment URL    | ✔️ Completed Render and Vercel links listed in “Deployment”. |

---

## Testing and Contribution

If pytest is installed inside the backend virtual environment, activate the venv and run:

```bash
cd backend
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pytest
```

### Contributing

Fork the repository, create a feature branch, commit your changes, and open a pull request.

---

## Architecture

```
User → Vercel Frontend (Next.js) → Render Backend (FastAPI)
                   ↘               ↘
                     OCR Engine (Tesseract) → Parser & LLM rules
                                 ↘
                           JSON response → Frontend display
```

- The Next.js frontend hosts the upload UI and result cards.
- FastAPI on Render receives PDFs, orchestrates OCR and parsing, and returns normalized JSON.
- Tesseract handles scanned/image PDFs; rule-based parsing plus LLM prompts extract allergens and nutrition.
- Results are rendered in both table and JSON tabs for review/export.

---

## Limitations & Future Work

### Current limitations
- Optimized for Hungarian and English PDFs; other languages may require new rules.
- Allergen list is fixed to the 10 items defined in the assignment.
- OCR-driven accuracy depends on source document quality (blurry scans reduce precision).

### Planned improvements
- Expand language coverage (Polish/German) with modular keyword packs.
- Enrich nutrition parsing with serving-size conversion and micronutrients.
- Provide a Docker Compose stack for streamlined local development and E2E testing.

---

## Documentation

- [Developer Guide](docs/Developer%20Guide.pdf)
- [User Guide](docs/User%20Guide.pdf)

---

## License & Acknowledgments

- **License:** MIT License — see `LICENSE`.
- **Acknowledgment:** This project was developed as part of the developer assignment supervised by Dr. Tamás Bérczes, University of Debrecen (2025).

---

NutriParse Reader · 2025
