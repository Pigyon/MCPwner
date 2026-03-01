FROM trufflesecurity/trufflehog:3.93.6 AS trufflehog

FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy trufflehog binary
COPY --from=trufflehog /usr/bin/trufflehog /usr/bin/trufflehog

# Copy requirements and install dependencies
COPY docker/secrets/trufflehog/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /service

# Copy service files
COPY docker/common /service/common
COPY docker/secrets/trufflehog/main.py .

# Expose service port
EXPOSE 8091

# Run the FastAPI service
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8091"]
