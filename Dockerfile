FROM python:3.11-slim

WORKDIR /app

# Copy requirements files
COPY requirements.txt ./

# Configure environment variables to avoid creating .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install dependencies with pip (avoiding uv)
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make the entrypoint script executable
RUN chmod +x /app/docker-entrypoint.sh

# Expose the port on which the application runs
EXPOSE 8000

# Use the entrypoint script to run migrations before starting the application
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
