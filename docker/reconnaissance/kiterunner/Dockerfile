# Stage 1: Download kiterunner binary
FROM alpine:3.19 AS builder

RUN apk add --no-cache curl tar \
    && curl -sL https://github.com/assetnote/kiterunner/releases/download/v1.0.2/kiterunner_1.0.2_linux_amd64.tar.gz \
       -o /tmp/kiterunner.tar.gz \
    && tar -xzf /tmp/kiterunner.tar.gz -C /usr/local/bin/ \
    && chmod +x /usr/local/bin/kr \
    && rm /tmp/kiterunner.tar.gz

# Stage 2: Install Python deps
FROM python:3.11-alpine AS deps

COPY docker/reconnaissance/kiterunner/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 3: Lean runtime
FROM alpine:3.19

RUN apk add --no-cache python3 curl

COPY --from=builder /usr/local/bin/kr /usr/local/bin/kr
COPY --from=deps /install /usr

WORKDIR /app

COPY docker/common /app/common
COPY docker/reconnaissance/kiterunner/main.py .

EXPOSE 8121

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8121"]
