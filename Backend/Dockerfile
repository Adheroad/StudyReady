# Base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PLAYWRIGHT_BROWSERS_PATH=/opt/playwright

# Set working directory
WORKDIR /app

# Install system dependencies
# gcc and libpq-dev are often needed for python-docx, psycopg2, etc.
# weasyprint needs libpango, output, etc.
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    poppler-utils \
    fonts-noto-core \
    fonts-indic \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright Chromium browser and its system dependencies
RUN mkdir -p /opt/playwright && \
    playwright install --with-deps chromium && \
    chmod -R 755 /opt/playwright

# Copy application code
COPY . .

# Create unprivileged user
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app && \
    chown -R appuser:appuser /opt/playwright

USER appuser

# Expose port
EXPOSE 8000

# Command matches docker-compose command override for development
CMD ["python3", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
