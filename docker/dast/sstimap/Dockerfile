# Stage 1: Install Python deps
FROM python:3.11-slim AS deps

COPY docker/dast/sstimap/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

ARG SSTIMAP_VERSION=1.3.3.7
RUN curl -fsSL "https://github.com/vladko312/SSTImap/archive/refs/tags/v${SSTIMAP_VERSION}.tar.gz" \
    | tar -xz -C /opt \
    && mv "/opt/SSTImap-${SSTIMAP_VERSION}" /opt/sstimap \
    && pip install --no-cache-dir -r /opt/sstimap/requirements.txt

COPY --from=deps /install /usr/local
WORKDIR /app

COPY docker/common /app/common
COPY docker/dast/sstimap/main.py .

EXPOSE 8164
CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8164"]
