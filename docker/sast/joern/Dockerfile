FROM ghcr.io/joernio/joern:v4.0.512

USER root

# Install Python and pip for FastAPI wrapper, plus curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY docker/sast/joern/requirements.txt .
RUN pip install --break-system-packages --no-cache-dir -r requirements.txt

WORKDIR /service

# Copy service files
COPY docker/common /service/common
COPY docker/sast/joern/main.py .
COPY docker/sast/joern/scan.sc .

# Expose service port
EXPOSE 8089

CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8089"]
