FROM mcr.microsoft.com/playwright/python:v1.35.0-jammy

WORKDIR /app

# Install system dependencies for OpenCV and Tesseract
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-hin \
    tesseract-ocr-eng \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Ensure playwright browsers are installed
RUN playwright install chromium

# Copy application source
COPY src/ /app/src/

# Expose port
EXPOSE 8080

# Start server
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
