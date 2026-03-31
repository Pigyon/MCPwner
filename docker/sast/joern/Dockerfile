# Stage 1: Download and install Joern
FROM eclipse-temurin:21-jdk-jammy AS builder

RUN apt-get update && apt-get install -y --no-install-recommends wget unzip \
    && rm -rf /var/lib/apt/lists/*

RUN wget -q https://github.com/joernio/joern/releases/latest/download/joern-install.sh \
    && chmod +x joern-install.sh \
    && ./joern-install.sh --install-dir=/opt/joern \
    && rm joern-install.sh

# Stage 2: Lean runtime with JRE only
FROM eclipse-temurin:21-jre-jammy

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy only the joern CLI from builder
COPY --from=builder /opt/joern /opt/joern
ENV PATH="/opt/joern/joern-cli:${PATH}"

COPY docker/sast/joern/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /service

COPY docker/common /service/common
COPY docker/sast/joern/main.py .
COPY docker/sast/joern/scan.sc .

EXPOSE 8089

CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8089"]
