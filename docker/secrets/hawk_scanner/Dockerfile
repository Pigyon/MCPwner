FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY docker/secrets/hawk_scanner/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /service

# Copy service files
COPY docker/common /service/common
COPY docker/secrets/hawk_scanner/main.py .

# Expose service port
EXPOSE 8094

# Run the FastAPI service
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8094"]
