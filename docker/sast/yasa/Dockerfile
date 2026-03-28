FROM debian:bookworm-slim

# Install dependencies: curl for download/healthcheck, unzip, ca-certificates, python3/pip for FastAPI
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    unzip \
    ca-certificates \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Download and install YASA v0.2.33 CLI (linux-x64)
RUN curl -fsSL \
    https://github.com/antgroup/YASA-Engine/releases/download/v0.2.33/yasa-linux-x64.zip \
    -o /tmp/yasa.zip \
    && unzip /tmp/yasa.zip -d /opt/yasa \
    && rm /tmp/yasa.zip \
    && chmod +x /opt/yasa/yasa

ENV PATH="/opt/yasa:${PATH}"

# Install FastAPI wrapper dependencies
COPY docker/sast/yasa/requirements.txt .
RUN pip install --break-system-packages --no-cache-dir -r requirements.txt

WORKDIR /service

COPY docker/common /service/common
COPY docker/sast/yasa/main.py .

EXPOSE 8090

CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8090"]
