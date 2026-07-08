# Stage 1: Install Python deps
FROM python:3.11-slim AS deps

COPY docker/dast/sqlmap/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Runtime — sqlmap ships its own Python, we add the FastAPI wrapper
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        curl ca-certificates git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir sqlmap

COPY --from=deps /install /usr/local
WORKDIR /app

COPY docker/common /app/common
COPY docker/dast/sqlmap/main.py .

EXPOSE 8160
CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8160"]
