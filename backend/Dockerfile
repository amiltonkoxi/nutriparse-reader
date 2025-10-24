FROM python:3.12-slim

# Keep Python fast and noiseless inside the container.
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# Install OCR and PDF dependencies required by the parser.
RUN apt-get update && apt-get install -y \
    tesseract-ocr tesseract-ocr-eng \
    libtesseract-dev poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies before copying the full source.
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Bring in the backend application code.
COPY . /app/

# Launch FastAPI under uvicorn respecting Render's PORT variable.
CMD ["bash", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
