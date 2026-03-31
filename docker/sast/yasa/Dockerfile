# Stage 1: Download YASA binary
FROM alpine:3.19 AS builder

RUN apk add --no-cache curl unzip \
    && curl -fsSL \
       https://github.com/antGroup/YASA-Engine/releases/download/v0.2.33/yasa-linux-x64.zip \
       -o /tmp/yasa.zip \
    && unzip /tmp/yasa.zip -d /opt/yasa \
    && rm /tmp/yasa.zip \
    && chmod +x /opt/yasa/yasa-engine-linux-x64 \
    && ln -s /opt/yasa/yasa-engine-linux-x64 /opt/yasa/yasa

# Stage 2: Slim runtime
FROM python:3.11-slim

COPY --from=builder /opt/yasa /opt/yasa
ENV PATH="/opt/yasa:${PATH}"

COPY docker/sast/yasa/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /service

COPY docker/common /service/common
COPY docker/sast/yasa/main.py .

EXPOSE 8095

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8095"]
