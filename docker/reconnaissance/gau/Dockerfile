# Stage 1: Build gau
FROM golang:1.21-alpine AS builder

RUN go install github.com/lc/gau/v2/cmd/gau@v2.2.4

# Stage 2: Install Python deps
FROM python:3.11-alpine AS deps

COPY docker/reconnaissance/gau/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 3: Lean runtime
FROM alpine:3.19

RUN apk add --no-cache python3 curl

COPY --from=builder /go/bin/gau /usr/local/bin/gau
COPY --from=deps /install /usr

WORKDIR /app

COPY docker/common /app/common
COPY docker/reconnaissance/gau/main.py .

EXPOSE 8115

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8115"]
