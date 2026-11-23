"""HTTP API.

Run locally:  uvicorn nutriparse.api:app --reload
"""

from __future__ import annotations

import logging
import os
import tempfile

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware

from . import SCHEMA_VERSION, __version__
from .extraction import PdfError, count_pages, ocr_languages
from .pipeline import analyze_pdf
from .schemas import ErrorResponse, ExtractionResult

log = logging.getLogger("nutriparse")

MAX_UPLOAD_MB = float(os.getenv("NUTRIPARSE_MAX_UPLOAD_MB", "15"))
MAX_PAGES = int(os.getenv("NUTRIPARSE_MAX_PAGES", "30"))
CHUNK = 1 << 20


# The project's own web app domains are always allowed, so a stale value in
# the hosting dashboard cannot break production. ALLOWED_ORIGINS adds more.
KNOWN_ORIGINS = [
    "https://nutriparsereader.vercel.app",
    "https://nutriparse-reader.vercel.app",
    "http://localhost:3000",
]
# Vercel preview deployments of this project only (team scope in the host name).
DEFAULT_ORIGIN_REGEX = r"^https://(?:food-pdf-extractor|nutriparse-reader)-[a-z0-9-]+-amilton-koxis-projects\.vercel\.app$"


def _origins() -> list[str]:
    extra = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]
    return list(dict.fromkeys(KNOWN_ORIGINS + extra))


app = FastAPI(
    title="NutriParse API",
    version=__version__,
    description="Evidence-first extraction of the 14 EU allergens and nutrition facts from food specification PDFs.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins(),
    allow_origin_regex=os.getenv("ALLOWED_ORIGIN_REGEX") or DEFAULT_ORIGIN_REGEX,
    allow_credentials=False,  # the API uses no cookies
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "engine_version": __version__,
        "schema_version": SCHEMA_VERSION,
        "ocr_languages": ocr_languages() or None,
    }


@app.post(
    "/extract",
    response_model=ExtractionResult,
    responses={413: {"model": ErrorResponse}, 415: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
async def extract(file: UploadFile = File(...)) -> ExtractionResult:
    limit = int(MAX_UPLOAD_MB * 1024 * 1024)
    fd, path = tempfile.mkstemp(suffix=".pdf")
    try:
        size = 0
        head = b""
        with os.fdopen(fd, "wb") as out:
            while chunk := await file.read(CHUNK):
                if not head:
                    head = chunk[:5]
                size += len(chunk)
                if size > limit:
                    raise HTTPException(413, f"File is larger than {MAX_UPLOAD_MB:g} MB.")
                out.write(chunk)
        if head != b"%PDF-":
            raise HTTPException(415, "Only PDF files are accepted.")
        try:
            pages = await run_in_threadpool(count_pages, path)
        except PdfError as exc:
            raise HTTPException(422, "The PDF could not be read.") from exc
        if pages > MAX_PAGES:
            raise HTTPException(422, f"The PDF has {pages} pages; the limit is {MAX_PAGES}.")
        # OCR is CPU bound: keep it off the event loop.
        return await run_in_threadpool(analyze_pdf, path, file.filename)
    finally:
        try:
            os.remove(path)
        except OSError:
            pass
