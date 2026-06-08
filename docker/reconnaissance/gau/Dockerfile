# Stage 1: Build gau
FROM golang:1.21-alpine AS builder

RUN go install github.com/lc/gau/v2/cmd/gau@v2.2.4

# Stage 2: Install Python deps
FROM python:3.11-alpine AS deps

COPY docker/reconnaissance/gau/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 3: Lean runtime
# Use python:3.11-alpine (matches the deps builder) to avoid a Python ABI
# mismatch between apk's python3 and the pip-compiled packages.
FROM python:3.11-alpine

RUN apk add --no-cache curl

COPY --from=builder /go/bin/gau /usr/local/bin/gau
COPY --from=deps /install /usr/local

WORKDIR /app

COPY docker/common /app/common
COPY docker/reconnaissance/gau/main.py .

EXPOSE 8115

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8115"]
