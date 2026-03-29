FROM eclipse-temurin:21-jdk-jammy

# Install Python, pip, curl for FastAPI wrapper and healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    curl \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install joern via official installer
RUN wget -q https://github.com/joernio/joern/releases/latest/download/joern-install.sh \
    && chmod +x joern-install.sh \
    && ./joern-install.sh --install-dir=/opt/joern \
    && rm joern-install.sh

ENV PATH="/opt/joern/joern-cli:${PATH}"

# Copy requirements and install dependencies
COPY docker/sast/joern/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /service

# Copy service files
COPY docker/common /service/common
COPY docker/sast/joern/main.py .
COPY docker/sast/joern/scan.sc .

EXPOSE 8089

CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8089"]
