FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Install hawk-scanner
RUN pip install hawk-scanner==0.3.37

# Install FastAPI and uvicorn
RUN pip install --no-cache-dir fastapi uvicorn

WORKDIR /service

# Copy service files
COPY docker/common /service/common
COPY docker/secrets/hawk_scanner/main.py .

# Expose service port
EXPOSE 8094

# Run the FastAPI service
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8094"]
