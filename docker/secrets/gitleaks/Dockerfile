FROM zricethezav/gitleaks:v8.30.0 AS gitleaks

FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy gitleaks binary
COPY --from=gitleaks /usr/bin/gitleaks /usr/bin/gitleaks

# Install FastAPI and uvicorn
RUN pip install --no-cache-dir fastapi uvicorn

WORKDIR /service

# Copy service files
# Note: We need to copy from the build context which is the project root
COPY docker/common /service/common
COPY docker/secrets/gitleaks/main.py .

# Expose service port
EXPOSE 8090

# Run the FastAPI service
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8090"]
