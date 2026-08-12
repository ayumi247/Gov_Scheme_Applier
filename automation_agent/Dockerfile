FROM mcr.microsoft.com/playwright/python:v1.35.0-jammy

WORKDIR /app

# Install system dependencies for OpenCV and Tesseract
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-hin \
    tesseract-ocr-eng \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Ensure playwright browsers are installed
RUN playwright install chromium

# Copy application source
COPY src/ /app/src/

# Memory optimizations for Render Free Tier
ENV PYTHONUNBUFFERED=1
ENV MALLOC_ARENA_MAX=2

# Expose port
EXPOSE 8080

# Start server using shell form to allow environment variable expansion
CMD uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8080}
