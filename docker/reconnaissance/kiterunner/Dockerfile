FROM alpine:3.19 AS builder

ENV KITERUNNER_VERSION=1.0.2
ENV KITERUNNER_SHA256=6f0b70aabf747de592445a690281897eebbc45927e9264185d34ffb11637613b
RUN apk add --no-cache curl tar \
    && curl -sL https://github.com/assetnote/kiterunner/releases/download/v${KITERUNNER_VERSION}/kiterunner_${KITERUNNER_VERSION}_linux_amd64.tar.gz \
       -o /tmp/kiterunner.tar.gz \
    && echo "${KITERUNNER_SHA256}  /tmp/kiterunner.tar.gz" | sha256sum -c - \
    && tar -xzf /tmp/kiterunner.tar.gz -C /usr/local/bin/ \
    && chmod +x /usr/local/bin/kr \
    && rm /tmp/kiterunner.tar.gz

FROM python:3.11-alpine AS deps

COPY docker/reconnaissance/kiterunner/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM alpine:3.19

RUN apk add --no-cache python3 curl

COPY --from=builder /usr/local/bin/kr /usr/local/bin/kr
COPY --from=deps /install /usr

WORKDIR /app

COPY docker/common /app/common
COPY docker/reconnaissance/kiterunner/main.py .

EXPOSE 8121

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8121"]
