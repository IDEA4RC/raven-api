FROM python:3.12-slim

WORKDIR /app

# System deps for psycopg2 and runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements separately to leverage docker layer caching
COPY requirements.txt ./

# Configure environment variables to avoid creating .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install dependencies with pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Expose the port on which the application runs
EXPOSE 8000

# Default command for production
ENV UVICORN_HOST=0.0.0.0
ENV UVICORN_PORT=8000
CMD ["uvicorn", "main:app", "--host", "${UVICORN_HOST}", "--port", "${UVICORN_PORT}"]
