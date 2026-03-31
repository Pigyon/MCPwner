# Stage 1: Install Python deps
FROM python:3.11-slim AS builder

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Lean runtime
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 -s /bin/bash mcpwner

WORKDIR /app

COPY --from=builder /install /usr/local

COPY src/ ./src/
COPY config/config.yaml ./config/

RUN mkdir -p /var/log/mcpwner && \
    chown -R mcpwner:mcpwner /var/log/mcpwner /app

USER mcpwner

ENV PYTHONPATH=/app/src

CMD ["python", "src/server.py"]
