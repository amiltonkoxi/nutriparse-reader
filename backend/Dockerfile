FROM python:3.12-slim

# System deps (Tesseract + Poppler for PDFs)
RUN apt-get update && apt-get install -y \
    tesseract-ocr tesseract-ocr-eng \
    libtesseract-dev poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependencies
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy app source
COPY backend/ /app/

# Run FastAPI app (Render provides $PORT, fallback = 10000)
CMD ["bash", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
