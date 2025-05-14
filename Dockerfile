FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv 

# Copy requirements files
COPY requirements.txt pyproject.toml ./

# Configure environment variables to avoid creating .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install dependencies using uv
RUN uv pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose the port on which the application runs
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
