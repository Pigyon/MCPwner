# hawk-scanner native deps need gcc + libglib2.0-dev in the builder stage.
FROM python:3.11-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libglib2.0-dev \
    && rm -rf /var/lib/apt/lists/*

COPY docker/secrets/hawk_scanner/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Runtime needs libgl1 + libglib2.0-0 for hawk-scanner's OpenCV stack.
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local

WORKDIR /service

COPY docker/common /service/common
COPY docker/secrets/hawk_scanner/main.py .

EXPOSE 8094

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8094"]
