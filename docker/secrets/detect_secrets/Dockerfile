FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install detect-secrets
RUN pip install detect-secrets==1.5.0

# Install FastAPI and uvicorn
RUN pip install --no-cache-dir fastapi uvicorn

WORKDIR /service

# Copy service files
COPY docker/common /service/common
COPY docker/secrets/detect_secrets/main.py .

# Expose service port
EXPOSE 8093

# Run the FastAPI service
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8093"]
