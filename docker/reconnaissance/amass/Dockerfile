# Stage 1: Build amass
FROM golang:1.24-alpine AS builder

RUN apk add --no-cache git && \
    go install -v github.com/owasp-amass/amass/v5/...@v5.0.1

# Stage 2: Install Python deps
FROM python:3.11-alpine AS deps

COPY docker/reconnaissance/amass/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 3: Lean runtime
FROM alpine:3.19

RUN apk add --no-cache python3 ca-certificates curl

COPY --from=builder /go/bin/amass /usr/local/bin/amass
COPY --from=deps /install /usr

WORKDIR /app

COPY docker/common /app/common
COPY docker/reconnaissance/amass/main.py .

EXPOSE 8111

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8111"]
