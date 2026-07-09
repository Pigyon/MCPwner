FROM golang:1.24-alpine AS builder

RUN apk add --no-cache git && \
    go install -v github.com/owasp-amass/amass/v5/...@v5.0.1

FROM python:3.11-alpine AS deps

COPY docker/reconnaissance/amass/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Match python:3.11-alpine to the deps builder to avoid ABI mismatch with apk python3.
FROM python:3.11-alpine

RUN apk add --no-cache ca-certificates curl

COPY --from=builder /go/bin/amass /usr/local/bin/amass
COPY --from=deps /install /usr/local

WORKDIR /app

COPY docker/common /app/common
COPY docker/reconnaissance/amass/main.py .

EXPOSE 8111

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8111"]
