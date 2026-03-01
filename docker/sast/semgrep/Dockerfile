FROM python:3.11-slim

# Install system dependencies (curl for healthcheck, git for semgrep)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY docker/sast/semgrep/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /service

# Copy service files
COPY docker/common /service/common
COPY docker/sast/semgrep/main.py .

# Expose service port
EXPOSE 8082

# Run the FastAPI service with uvicorn
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8082"]
