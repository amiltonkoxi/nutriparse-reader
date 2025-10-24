from __future__ import annotations

import re
from typing import List

import pdfplumber
import pypdfium2 as pdfium
from unidecode import unidecode

def _normalize(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)     # glue hyphenated wraps
    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    text = re.sub(r"(\d),(\d)", r"\1.\2", text)            # normalize decimal comma
    text = unidecode(text).lower()
    return text.strip()


def _extract_with_pdfplumber(pdf_path: str) -> str:
    chunks: List[str] = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for p in pdf.pages:
                t = p.extract_text() or ""
                if t:
                    chunks.append(t)
    except Exception:
        return ""
    return "\n".join(chunks)


def _extract_with_pdfium(pdf_path: str) -> str:
    try:
        doc = pdfium.PdfDocument(pdf_path)
    except Exception:
        return ""

    texts: List[str] = []
    try:
        for index in range(len(doc)):
            page = doc.get_page(index)
            try:
                textpage = page.get_textpage()
                try:
                    snippet = textpage.get_text_range() or ""
                    if snippet:
                        texts.append(snippet)
                finally:
                    textpage.close()
            finally:
                page.close()
    finally:
        doc.close()
    return "\n".join(texts)


def extract_text(pdf_path: str) -> str:
    """Try PyPDFium2 first for layout fidelity, fall back to pdfplumber."""
    raw_pdfium = _extract_with_pdfium(pdf_path)
    raw_plumber = _extract_with_pdfplumber(pdf_path)

    if raw_pdfium and raw_plumber:
        if raw_plumber in raw_pdfium:
            raw = raw_pdfium
        elif raw_pdfium in raw_plumber:
            raw = raw_plumber
        else:
            raw = f"{raw_pdfium}\n\n{raw_plumber}"
    else:
        raw = raw_pdfium or raw_plumber

    return _normalize(raw)
