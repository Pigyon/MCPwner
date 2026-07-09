FROM alpine:3.19 AS builder

ARG DALFOX_VERSION=2.9.3
RUN apk add --no-cache curl \
    && curl -fsSL "https://github.com/hahwul/dalfox/releases/download/v${DALFOX_VERSION}/dalfox_${DALFOX_VERSION}_linux_amd64.tar.gz" \
       -o /tmp/dalfox.tar.gz \
    && tar -xzf /tmp/dalfox.tar.gz -C /usr/local/bin/ dalfox \
    && chmod +x /usr/local/bin/dalfox \
    && rm /tmp/dalfox.tar.gz

FROM python:3.11-alpine AS deps

COPY docker/dast/dalfox/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM alpine:3.19

RUN apk add --no-cache python3 curl

COPY --from=builder /usr/local/bin/dalfox /usr/local/bin/dalfox
COPY --from=deps /install /usr

WORKDIR /app

COPY docker/common /app/common
COPY docker/dast/dalfox/main.py .

EXPOSE 8163

CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8163"]
