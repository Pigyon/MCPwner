FROM python:3.11-slim

# Install git for repository cloning
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash mcpwner

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY config/config.yaml ./config/

# Create necessary directories
RUN mkdir -p /var/log/mcpwner && \
    chown -R mcpwner:mcpwner /var/log/mcpwner /app

# Switch to non-root user
USER mcpwner

# Set PYTHONPATH so imports work correctly
ENV PYTHONPATH=/app/src

CMD ["python", "src/server.py"]